use tauri::{
    plugin::{Builder as PluginBuilder, TauriPlugin},
    webview::PageLoadEvent,
    Manager, Runtime,
};

const EULER_URL: &str = "https://euler-app-beta.onrender.com";
const EULER_HOST: &str = "euler-app-beta.onrender.com";
const RETRY_HOST: &str = "retry.euler.local";

fn startup_navigation<R: Runtime>() -> TauriPlugin<R> {
    PluginBuilder::new("euler-startup")
        .on_navigation(|webview, url| match webview.label() {
            "splash" => {
                if url.scheme() == "https" && url.host_str() == Some(RETRY_HOST) {
                    if let Some(main) = webview.app_handle().get_webview_window("main") {
                        let _ = main.hide();
                        if let Ok(remote) = tauri::Url::parse(EULER_URL) {
                            let _ = main.navigate(remote);
                        }
                    }
                    false
                } else {
                    url.scheme() == "tauri"
                        || url.host_str() == Some("tauri.localhost")
                        || (cfg!(debug_assertions) && url.host_str() == Some("localhost"))
                }
            }
            "main" => url.scheme() == "https" && url.host_str() == Some(EULER_HOST),
            _ => false,
        })
        .build()
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(startup_navigation())
        .on_page_load(|webview, payload| {
            if webview.label() != "main"
                || !matches!(payload.event(), PageLoadEvent::Finished)
                || payload.url().scheme() != "https"
                || payload.url().host_str() != Some(EULER_HOST)
            {
                return;
            }

            if let Some(main) = webview.app_handle().get_webview_window("main") {
                let _ = main.show();
                let _ = main.set_focus();
            }

            if let Some(splash) = webview.app_handle().get_webview_window("splash") {
                let _ = splash.hide();
            }
        })
        .on_window_event(|window, event| {
            if !matches!(event, tauri::WindowEvent::CloseRequested { .. }) {
                return;
            }

            match window.label() {
                "splash" => {
                    if let Some(main) = window.app_handle().get_webview_window("main") {
                        let _ = main.destroy();
                    }
                }
                "main" => {
                    if let Some(splash) = window.app_handle().get_webview_window("splash") {
                        let _ = splash.destroy();
                    }
                }
                _ => {}
            }
        })
        .run(tauri::generate_context!())
        .expect("erro ao iniciar o EULER");
}
