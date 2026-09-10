use serde::{Deserialize, Serialize};
use std::collections::BTreeMap;

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum BreakingSeverity {
    Info,
    Warning,
    Breaking,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub enum ChangeKind {
    EndpointAdded,
    EndpointRemoved,
    ParameterAdded { required: bool },
    ParameterRemoved,
    ParameterTypeChanged { from: String, to: String },
    ParameterRequiredChanged { was: bool, now: bool },
    ResponseFieldAdded,
    ResponseFieldRemoved,
    ResponseFieldTypeChanged { from: String, to: String },
    ResponseStatusAdded { status: String },
    ResponseStatusRemoved { status: String },
}

pub struct FieldChange {
    pub field_path: String,
    pub kind: ChangeKind,
    pub severity: BreakingSeverity,
    pub description: String,
}

pub struct EndpointChange {
    pub path: String,
    pub method: String,
    pub changes: Vec<FieldChange>,
}

pub struct SpecInfo {
    pub title: String,
    pub version: String,
    pub endpoint_count: usize,
}

pub struct SchemaDiff {
    pub old_spec: SpecInfo,
    pub new_spec: SpecInfo,
    pub endpoint_changes: Vec<EndpointChange>,
    pub breaking_count: usize,
    pub warning_count: usize,
    pub info_count: usize,
}

pub struct ParsedEndpoint {
    pub path: String,
    pub method: String,
    pub parameters: BTreeMap<String, ParsedParam>,
    pub response_fields: BTreeMap<String, ParsedField>,
    pub response_statuses: Vec<String>,
}

pub struct ParsedParam {
    pub name: String,
    pub location: String, // query, path, header, cookie
    pub param_type: String,
    pub required: bool,
}

pub struct ParsedField {
    pub name: String,
    pub field_type: String,
}

pub struct ParsedSpec {
    pub info: SpecInfo,
    pub endpoints: BTreeMap<String, ParsedEndpoint>,
}
