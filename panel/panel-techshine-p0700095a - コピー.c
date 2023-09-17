// SPDX-License-Identifier: GPL-2.0+
/*
 * Copyright 2022 Panasonic Corporation
 */

#include <linux/delay.h>
#include <linux/gpio/consumer.h>
#include <linux/module.h>
#include <linux/of.h>
#include <linux/regulator/consumer.h>

#include <video/mipi_display.h>

#include <drm/drm_crtc.h>
#include <drm/drm_device.h>
#include <drm/drm_mipi_dsi.h>
#include <drm/drm_modes.h>
#include <drm/drm_panel.h>

struct techshine_panel {
	struct drm_panel base;
	struct mipi_dsi_device *link;

	struct regulator *supply;
	struct gpio_desc *reset_gpio;
	struct gpio_desc *stbyb_gpio;

	bool prepared;
	bool enabled;
};

static inline
struct techshine_panel *to_techshine_panel(struct drm_panel *panel)
{
	return container_of(panel, struct techshine_panel, base);
}

static int techshine_panel_disable(struct drm_panel *panel)
{
	struct techshine_panel *techshine = to_techshine_panel(panel);

	if (!techshine->enabled)
		return 0;

	mipi_dsi_dcs_set_display_off(techshine->link);

	techshine->enabled = false;

	return 0;
}

static int techshine_panel_enable(struct drm_panel *panel)
{
	struct techshine_panel *techshine = to_techshine_panel(panel);
	int err;

	if (techshine->enabled)
		return 0;

	err = mipi_dsi_dcs_set_display_on(techshine->link);
	if (err < 0) {
		dev_err(panel->dev, "failed to set display on: %d\n", err);
		return err;
	}

	techshine->enabled = true;

	return 0;
}

static int techshine_panel_unprepare(struct drm_panel *panel)
{
	struct techshine_panel *techshine = to_techshine_panel(panel);

	if (!techshine->prepared)
		return 0;

	mipi_dsi_dcs_enter_sleep_mode(techshine->link);

	msleep(120);

	gpiod_set_value_cansleep(techshine->stbyb_gpio, 1);

	msleep(20);

	gpiod_set_value_cansleep(techshine->reset_gpio, 1);

	msleep(20);

	regulator_disable(techshine->supply);

	techshine->prepared = false;

	return 0;
}

static int techshine_panel_prepare(struct drm_panel *panel)
{
	struct techshine_panel *techshine = to_techshine_panel(panel);
	int err;

	if (techshine->prepared)
		return 0;

	err = regulator_enable(techshine->supply);
	if (err < 0) {
		dev_err(panel->dev, "failed to regulator enable: %d\n", err);
		return err;
	}

	msleep(20);

	gpiod_set_value_cansleep(techshine->reset_gpio, 0);

	msleep(20);

	gpiod_set_value_cansleep(techshine->stbyb_gpio, 0);

	msleep(20);

	err = mipi_dsi_dcs_exit_sleep_mode(techshine->link);
	if (err < 0) {
		dev_err(panel->dev, "failed to exit sleep mode: %d\n", err);
		goto poweroff;
	}

	msleep(120);

	techshine->prepared = true;

	return 0;

poweroff:
	gpiod_set_value_cansleep(techshine->stbyb_gpio, 1);
	msleep(20);
	gpiod_set_value_cansleep(techshine->reset_gpio, 1);
	msleep(20);
	regulator_disable(techshine->supply);

	return err;
}

static const struct drm_display_mode default_mode = {
	.clock = 51668,
	.hdisplay = 1024,
	.hsync_start = 1024 + 160,
	.hsync_end = 1024 + 160 + 10,
	.htotal = 1024 + 160 + 10 + 160,
	.vdisplay = 600,
	.vsync_start = 600 + 12,
	.vsync_end = 600 + 12 + 1,
	.vtotal = 600 + 12 + 1 + 23,
	.flags = DRM_MODE_FLAG_NHSYNC | DRM_MODE_FLAG_NVSYNC,
	.width_mm = 154,
	.height_mm = 86,
};

static int techshine_panel_get_modes(struct drm_panel *panel,
				       struct drm_connector *connector)
{
	struct drm_display_mode *mode;

	mode = drm_mode_duplicate(connector->dev, &default_mode);
	if (!mode) {
		dev_err(panel->dev, "failed to add mode %ux%u@%u\n",
			default_mode.hdisplay, default_mode.vdisplay,
			drm_mode_vrefresh(&default_mode));
		return -ENOMEM;
	}

	drm_mode_set_name(mode);

	mode->type = DRM_MODE_TYPE_DRIVER | DRM_MODE_TYPE_PREFERRED;
	connector->display_info.width_mm = mode->width_mm;
	connector->display_info.height_mm = mode->height_mm;
	drm_mode_probed_add(connector, mode);

	return 1;
}

static const struct drm_panel_funcs techshine_panel_funcs = {
	.disable = techshine_panel_disable,
	.unprepare = techshine_panel_unprepare,
	.prepare = techshine_panel_prepare,
	.enable = techshine_panel_enable,
	.get_modes = techshine_panel_get_modes,
};

static const struct of_device_id techshine_of_match[] = {
	{ .compatible = "techshine,p0700095a", },
	{ }
};
MODULE_DEVICE_TABLE(of, techshine_of_match);

static int techshine_panel_add(struct techshine_panel *techshine)
{
	struct device *dev = &techshine->link->dev;
	int err;

	techshine->supply = devm_regulator_get(dev, "power");
	if (IS_ERR(techshine->supply)) {
		err = PTR_ERR(techshine->supply);
		dev_err(dev, "failed to request regulator: %d\n", err);
		return err;
	}

	techshine->reset_gpio = devm_gpiod_get_optional(dev, "reset",
							   GPIOD_OUT_HIGH);
	if (IS_ERR(techshine->reset_gpio)) {
		err = PTR_ERR(techshine->reset_gpio);
		dev_err(dev, "failed to get reset gpio: %d\n", err);
		return err;
	}

	techshine->stbyb_gpio = devm_gpiod_get_optional(dev, "stbyb",
							   GPIOD_OUT_HIGH);
	if (IS_ERR(techshine->stbyb_gpio)) {
		err = PTR_ERR(techshine->stbyb_gpio);
		dev_err(dev, "failed to get stbyb gpio: %d\n", err);
		return err;
	}

	drm_panel_init(&techshine->base, &techshine->link->dev,
		       &techshine_panel_funcs, DRM_MODE_CONNECTOR_DSI);

	err = drm_panel_of_backlight(&techshine->base);
	if (err)
		return err;

	drm_panel_add(&techshine->base);

	return 0;
}

static void techshine_panel_del(struct techshine_panel *techshine)
{
	drm_panel_remove(&techshine->base);
}

static int techshine_panel_probe(struct mipi_dsi_device *dsi)
{
	struct techshine_panel *techshine;
	int err;

	dsi->lanes = 4;
	dsi->format = MIPI_DSI_FMT_RGB888;
	dsi->mode_flags = MIPI_DSI_MODE_VIDEO | MIPI_DSI_MODE_VIDEO_SYNC_PULSE;

	techshine = devm_kzalloc(&dsi->dev, sizeof(*techshine), GFP_KERNEL);
	if (!techshine)
		return -ENOMEM;

	mipi_dsi_set_drvdata(dsi, techshine);
	techshine->link = dsi;

	err = techshine_panel_add(techshine);
	if (err < 0)
		return err;

	return mipi_dsi_attach(dsi);
}

static int techshine_panel_remove(struct mipi_dsi_device *dsi)
{
	struct techshine_panel *techshine = mipi_dsi_get_drvdata(dsi);

	drm_panel_disable(&techshine->base);
	drm_panel_unprepare(&techshine->base);
	mipi_dsi_detach(dsi);
	techshine_panel_del(techshine);

	return 0;
}

static void techshine_panel_shutdown(struct mipi_dsi_device *dsi)
{
	struct techshine_panel *techshine = mipi_dsi_get_drvdata(dsi);

	drm_panel_disable(&techshine->base);
	drm_panel_unprepare(&techshine->base);
}

static struct mipi_dsi_driver techshine_panel_driver = {
	.driver = {
		.name = "panel-techshine-p0700095a",
		.of_match_table = techshine_of_match,
	},
	.probe = techshine_panel_probe,
	.remove = techshine_panel_remove,
	.shutdown = techshine_panel_shutdown,
};
module_mipi_dsi_driver(techshine_panel_driver);

MODULE_DESCRIPTION("techshine p0700095a panel driver");
MODULE_LICENSE("GPL v2");
