use std::fs;
use std::io::Write;
use std::path::Path;
use std::process::{Command, Stdio};
use std::thread;
use std::time::Duration;
use std::env;

use reqwest::blocking::Client;

#[cfg(windows)]
use std::os::windows::process::CommandExt;

fn main() {
   
    let script_path = get_script_path();

    let python_installed = check_python();

    if !python_installed {
        if ask_to_install_python() {
            install_python_silent();
            thread::sleep(Duration::from_secs(5));
            if !check_python() {
                show_message("❌ Python installation failed. Please install manually.");
                return;
            }
        } else {
            return;
        }
    }

  
    if let Some(parent) = script_path.parent() {
        if !parent.exists() {
      
            if let Err(e) = fs::create_dir_all(parent) {
           
                let fallback = get_fallback_path();
                if let Some(fb_parent) = fallback.parent() {
                    let _ = fs::create_dir_all(fb_parent);
                }
             
                let fallback_path = get_fallback_path();
             
                if download_script(&fallback_path) {
                    run_script(&fallback_path);
                } else {
                    show_message("❌ Failed to download idle.py.");
                }
                return;
            }
        }
    }


    if !download_script(&script_path) {
        show_message("❌ Failed to download idle.py.");
        return;
    }

    run_script(&script_path);
}

fn get_script_path() -> std::path::PathBuf {
    let program_files = if cfg!(windows) {
        env::var("ProgramFiles").unwrap_or_else(|_| "C:\\Program Files".to_string())
    } else {
        "/usr/local".to_string()
    };
    std::path::PathBuf::from(program_files).join("py pro").join("idle.py")
}

// ------------------------------------------------------------
fn get_fallback_path() -> std::path::PathBuf {
    let app_data = if cfg!(windows) {
        env::var("LOCALAPPDATA").unwrap_or_else(|_| {
            let home = env::var("USERPROFILE").unwrap_or_else(|_| ".".to_string());
            format!("{}\\AppData\\Local", home)
        })
    } else {
        env::var("HOME").unwrap_or_else(|_| ".".to_string())
    };
    std::path::PathBuf::from(app_data).join("py pro").join("idle.py")
}

fn check_python() -> bool {
    let python_cmd = if cfg!(windows) { "python" } else { "python3" };
    Command::new(python_cmd)
        .arg("--version")
        .stdout(Stdio::null())
        .stderr(Stdio::null())
        .status()
        .map(|s| s.success())
        .unwrap_or(false)
}

fn ask_to_install_python() -> bool {
    #[cfg(windows)]
    {
        use winapi::um::winuser::{MessageBoxW, MB_YESNO, MB_ICONQUESTION, MB_DEFBUTTON1};
        use std::ffi::OsStr;
        use std::iter::once;
        use std::os::windows::ffi::OsStrExt;
        use std::ptr::null_mut;

        let title = "Python IDLE Pro";
        let message = "Python is not installed on your system.\n\nDo you want to install it now?";
        
        let title_wide: Vec<u16> = OsStr::new(title)
            .encode_wide()
            .chain(once(0))
            .collect();
        let msg_wide: Vec<u16> = OsStr::new(message)
            .encode_wide()
            .chain(once(0))
            .collect();

        let result = unsafe {
            MessageBoxW(
                null_mut(),
                msg_wide.as_ptr(),
                title_wide.as_ptr(),
                MB_YESNO | MB_ICONQUESTION | MB_DEFBUTTON1,
            )
        };
        return result == 6;
    }

    #[cfg(not(windows))]
    {
  
        let output = Command::new("zenity")
            .args([
                "--question",
                "--text=Python is not installed. Do you want to install it now?",
                "--title=Python IDLE Pro",
                "--ok-label=Yes",
                "--cancel-label=No",
            ])
            .status();

        if let Ok(status) = output {
            return status.success();
        }

        println!("Python is not installed.");
        println!("Do you want to install it now? (y/n): ");
        let mut input = String::new();
        std::io::stdin().read_line(&mut input).unwrap();
        input.trim().to_lowercase() == "y"
    }
}

fn install_python_silent() {
    let installer_url = "https://www.python.org/ftp/python/3.12.5/python-3.12.5-amd64.exe";
    let installer_path = "python_installer.exe";

    match download_file(installer_url, installer_path) {
        Ok(_) => {
            #[cfg(windows)]
            {
                let _ = Command::new(installer_path)
                    .args(["/quiet", "InstallAllUsers=0", "PrependPath=1", "Include_test=0"])
                    .stdout(Stdio::null())
                    .stderr(Stdio::null())
                    .spawn()
                    .unwrap()
                    .wait();
                let _ = fs::remove_file(installer_path);
            }

            #[cfg(not(windows))]
            {
                show_message("Please install Python manually from python.org");
                let _ = webbrowser::open("https://www.python.org/downloads/");
            }
        }
        Err(e) => {
            show_message(&format!("Failed to download Python installer: {}", e));
            let _ = webbrowser::open("https://www.python.org/downloads/");
        }
    }
}

fn download_file(url: &str, dest: &str) -> Result<(), String> {
    let client = Client::builder()
        .timeout(Duration::from_secs(60))
        .build()
        .map_err(|e| e.to_string())?;

    let response = client
        .get(url)
        .send()
        .map_err(|e| format!("Connection failed: {}", e))?;

    if !response.status().is_success() {
        return Err(format!("HTTP {}", response.status()));
    }

    let bytes = response
        .bytes()
        .map_err(|e| format!("Failed to read data: {}", e))?;

    let mut file = fs::File::create(dest).map_err(|e| format!("Failed to create file: {}", e))?;
    file.write_all(&bytes).map_err(|e| format!("Failed to write: {}", e))?;

    Ok(())
}

fn download_script(path: &Path) -> bool {
    let url = "https://raw.githubusercontent.com/857seif/python-idle-pro/main/idle.py";
    match download_file(url, path.to_str().unwrap()) {
        Ok(_) => true,
        Err(e) => {
            show_message(&format!("Failed to download script: {}", e));
            false
        }
    }
}

fn run_script(path: &Path) {
    let python_cmd = if cfg!(windows) { "python" } else { "python3" };

    #[cfg(windows)]
    {
        let _ = Command::new(python_cmd)
            .arg(path.to_str().unwrap())
            .stdout(Stdio::null())
            .stderr(Stdio::null())
            .creation_flags(0x08000000) 
            .spawn();
    }

    #[cfg(not(windows))]
    {
        let _ = Command::new(python_cmd)
            .arg(path.to_str().unwrap())
            .stdout(Stdio::null())
            .stderr(Stdio::null())
            .spawn();
    }

    thread::sleep(Duration::from_millis(300));
}

fn show_message(text: &str) {
    #[cfg(windows)]
    {
        use winapi::um::winuser::{MessageBoxW, MB_OK, MB_ICONERROR};
        use std::ffi::OsStr;
        use std::iter::once;
        use std::os::windows::ffi::OsStrExt;
        use std::ptr::null_mut;

        let title = "Python IDLE Pro";
        let msg_wide: Vec<u16> = OsStr::new(text)
            .encode_wide()
            .chain(once(0))
            .collect();
        let title_wide: Vec<u16> = OsStr::new(title)
            .encode_wide()
            .chain(once(0))
            .collect();

        unsafe {
            MessageBoxW(
                null_mut(),
                msg_wide.as_ptr(),
                title_wide.as_ptr(),
                MB_OK | MB_ICONERROR,
            );
        }
    }

    #[cfg(not(windows))]
    {
        let _ = Command::new("zenity")
            .args(["--error", "--text", text, "--title", "Python IDLE Pro"])
            .status();
        eprintln!("{}", text);
    }
}