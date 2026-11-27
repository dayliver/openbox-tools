#include <geanyplugin.h>

static const gchar scheme_name[] = "openbox-tools.conf";

static void
reload_palette(GObject *settings, GParamSpec *property, gpointer data)
{
    GeanyPlugin *plugin = data;
    gchar *theme = NULL;
    g_object_get(settings, "gtk-theme-name", &theme, NULL);
    gboolean managed = theme && g_str_has_prefix(theme, "Openbox-Tools-Thunar-");
    g_free(theme);
    if (!managed)
        return;

    GeanyEditorPrefs *prefs = plugin->geany_data->editor_prefs;
    g_free(prefs->color_scheme);
    prefs->color_scheme = g_strdup(scheme_name);
    main_reload_configuration();
}

static gboolean
init(GeanyPlugin *plugin, gpointer data)
{
    plugin_signal_connect(plugin, G_OBJECT(gtk_settings_get_default()),
                          "notify::gtk-theme-name", FALSE,
                          G_CALLBACK(reload_palette), plugin);
    return TRUE;
}

static void
cleanup(GeanyPlugin *plugin, gpointer data)
{
    /* Geany disconnects plugin_signal_connect handlers on unload. */
}

G_MODULE_EXPORT void
geany_load_module(GeanyPlugin *plugin)
{
    plugin->info->name = "Archcraft Palette";
    plugin->info->description = "Refresh the editor palette when Archcraft updates the GTK theme.";
    plugin->info->version = "1.0";
    plugin->info->author = "openbox-tools";
    plugin->funcs->init = init;
    plugin->funcs->cleanup = cleanup;
    GEANY_PLUGIN_REGISTER(plugin, 225);
}
