use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub enum CallsiteKind {
    Import,
    MethodCall,
    UrlReference,
    TypeReference,
}

pub struct Callsite {
    pub file_path: String,
    pub line_number: usize,
    pub column: usize,
    pub line_content: String,
    pub kind: CallsiteKind,
    pub matched_pattern: String,
    pub alias: Option<String>, // Local client identifier; None for canonical refs.
}

pub struct ScanConfig {
    pub sdk_names: Vec<String>,
    pub api_base_urls: Vec<String>,
    pub method_patterns: Vec<String>,
    pub extensions: Vec<String>,
}

fn default_extensions() -> Vec<String> {
    vec![
        "ts".into(),
        "tsx".into(),
        "js".into(),
        "jsx".into(),
        "mjs".into(),
        "py".into(),
        "go".into(),
        "rs".into(),
    ]
}

impl Default for ScanConfig {
    fn default() -> Self {
        Self {
            sdk_names: Vec::new(),
            api_base_urls: Vec::new(),
            method_patterns: Vec::new(),
            extensions: default_extensions(),
        }
    }
}

pub struct ScanResult {
    pub callsites: Vec<Callsite>,
    pub files_scanned: usize,
    pub files_with_hits: usize,
}

impl ScanResult {
    pub fn affected_files(&self) -> Vec<String> {
        let mut files: Vec<String> = self.callsites.iter().map(|c| c.file_path.clone()).collect();
        files.sort();
        files.dedup();
        files
    }
}
