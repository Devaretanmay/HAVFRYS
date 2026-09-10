/// Kernel-enforced sandboxing for execution sessions.

mod linux;

mod macos;

pub struct SandboxInfo {
    pub supported: bool,
    pub platform: String,
    pub details: String,
}

pub fn apply(worktree_path: &str, block_network: bool) -> Result<(), String> {
    {
        linux::apply(worktree_path, block_network)
    }

    {
        macos::apply(worktree_path, block_network)
    }

    {
        let _ = (worktree_path, block_network);
        Err(format!(
            "Sandboxing not supported on '{}' (requires Linux with Landlock or macOS with Seatbelt)",
            std::env::consts::OS
        ))
    }
}

pub fn check_supported() -> bool {
    {
        linux::check_supported()
    }

    {
        macos::check_supported()
    }

    {
        false
    }
}

pub fn get_info() -> SandboxInfo {
    {
        linux::get_info()
    }

    {
        macos::get_info()
    }

    {
        SandboxInfo {
            supported: false,
            platform: std::env::consts::OS.to_string(),
            details: format!(
                "Platform '{}' is not supported. Requires Linux (5.13+) with Landlock or macOS with Seatbelt.",
                std::env::consts::OS
            ),
        }
    }
}
