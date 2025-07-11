import json
from typing import Dict, List, Any
from pathlib import Path
import glob
import os
import re

def convert_legal_json_to_markdown(json_data: Dict[str, Any]) -> str:
    """
    Convert legal case JSON to formatted Markdown
    
    Args:
        json_data: Dictionary following the legal case JSON schema
        
    Returns:
        Formatted Markdown string
    """
    md_content = []
    
    # Document metadata
    doc_meta = json_data.get("document_metadata", {})
    total_cases = doc_meta.get("total_cases", 1)
    
    # Process each case
    cases = json_data.get("cases", [])
    
    for case_idx, case in enumerate(cases):
        # Add case separator for multiple cases
        if total_cases > 1:
            if case_idx > 0:
                md_content.append("\n---\n\n")
            md_content.append(f"# CASE {case.get('case_number', case_idx + 1)}\n\n")
        
        # Case title and metadata
        case_meta = case.get("case_metadata", {})
        case_title = case_meta.get("case_title", "Legal Case")
        
        if total_cases == 1:
            md_content.append(f"# {case_title}\n\n")
        else:
            md_content.append(f"## {case_title}\n\n")
        
        # Case details table
        md_content.append(_format_case_metadata(case_meta))
        
        # Parties section
        parties = case.get("parties", {})
        md_content.append(_format_parties(parties))
        
        # Tribunal/Court composition
        tribunal_members = case.get("tribunal_members", [])
        if tribunal_members:
            md_content.append(_format_tribunal_members(tribunal_members))
        
        # Appearances
        appearances = case.get("appearances", [])
        if appearances:
            md_content.append(_format_appearances(appearances))
        
        md_content.append("---\n\n")
        
        # Main content sections
        sections = case.get("sections", [])
        md_content.append(_format_sections(sections))
        
        # Signatures
        signatures = case.get("signatures", [])
        if signatures:
            md_content.append(_format_signatures(signatures))
        
        # Footnotes
        footnotes = case.get("footnotes", [])
        if footnotes:
            md_content.append(_format_footnotes(footnotes))
    
    return "".join(md_content)

def _format_case_metadata(case_meta: Dict[str, Any]) -> str:
    """Format case metadata as a details section"""
    content = []
    
    # Key metadata fields
    metadata_fields = [
        ("Decision No.", "decision_number"),
        ("Reference No.", "reference_number"),
        ("Court/Tribunal", "court_tribunal"),
        ("Jurisdiction", "jurisdiction"),
        ("Legal Basis", "legal_basis"),
        ("Decision Type", "decision_type"),
        ("Hearing Date", "hearing_date"),
        ("Decision Date", "decision_date")
    ]
    
    for label, key in metadata_fields:
        value = case_meta.get(key)
        if value:
            content.append(f"**{label}:** {value}  \n")
    
    if content:
        content.insert(0, "## Case Details\n\n")
        content.append("\n")
    
    return "".join(content)

def _format_parties(parties: Dict[str, Any]) -> str:
    """Format parties section"""
    content = ["## Parties\n\n"]
    
    # Plaintiffs
    plaintiffs = parties.get("plaintiffs", [])
    if plaintiffs:
        content.append("### Plaintiff" + ("s" if len(plaintiffs) > 1 else "") + "\n")
        for plaintiff in plaintiffs:
            name = plaintiff.get("name", "")
            role = plaintiff.get("role", "")
            party_type = plaintiff.get("type", "")
            content.append(f"- **{name}** ({role}, {party_type})\n")
        content.append("\n")
    
    # Defendants
    defendants = parties.get("defendants", [])
    if defendants:
        content.append("### Defendant" + ("s" if len(defendants) > 1 else "") + "\n")
        for defendant in defendants:
            name = defendant.get("name", "")
            role = defendant.get("role", "")
            party_type = defendant.get("type", "")
            content.append(f"- **{name}** ({role}, {party_type})\n")
        content.append("\n")
    
    # Other parties
    other_parties = parties.get("other_parties", [])
    if other_parties:
        content.append("### Other Parties\n")
        for party in other_parties:
            name = party.get("name", "")
            role = party.get("role", "")
            content.append(f"- **{name}** ({role})\n")
        content.append("\n")
    
    return "".join(content)

def _format_tribunal_members(tribunal_members: List[Dict[str, Any]]) -> str:
    """Format tribunal/court members"""
    content = ["## Tribunal Members\n"]
    
    for member in tribunal_members:
        name = member.get("name", "")
        role = member.get("role", "")
        content.append(f"- **{name}** - {role}\n")
    
    content.append("\n")
    return "".join(content)

def _format_appearances(appearances: List[Dict[str, Any]]) -> str:
    """Format legal appearances"""
    content = ["## Appearances\n"]
    
    for appearance in appearances:
        counsel = appearance.get("counsel", "")
        representing = appearance.get("representing", "")
        content.append(f"- **{counsel}** for {representing}\n")
    
    content.append("\n")
    return "".join(content)

def _format_sections(sections: List[Dict[str, Any]]) -> str:
    """Format main content sections"""
    content = []
    
    for section in sections:
        title = section.get("title", "")
        if title:
            content.append(f"## {title.upper()}\n\n")
        
        paragraphs = section.get("paragraphs", [])
        content.append(_format_paragraphs(paragraphs))
    
    return "".join(content)

def _format_paragraphs(paragraphs: List[Dict[str, Any]]) -> str:
    """Format paragraphs within a section"""
    content = []
    
    for para in paragraphs:
        number = para.get("number", "")
        para_content = para.get("content", "")
        
        # Format paragraph header and content on same line
        if number:
            # Handle quoted material
            quoted_material = para.get("quoted_material", {})
            if quoted_material and quoted_material.get("content"):
                content.append(f"### {number}\n")
                content.append(_format_quoted_material(quoted_material, para_content))
            else:
                # Regular paragraph content with inline footnote processing
                formatted_content = _process_footnote_references(para_content)
                content.append(f"### {number}\n{formatted_content}\n\n")
        else:
            # Handle quoted material
            quoted_material = para.get("quoted_material", {})
            if quoted_material and quoted_material.get("content"):
                content.append(_format_quoted_material(quoted_material, para_content))
            else:
                # Regular paragraph content with inline footnote processing
                formatted_content = _process_footnote_references(para_content)
                content.append(f"{formatted_content}\n\n")
        
        # Add citations if any
        citations = para.get("citations", [])
        if citations:
            content.append(_format_citations(citations))
        
        # Add subsections if any
        subsections = para.get("subsections", [])
        if subsections:
            content.append(_format_subsections(subsections))
    
    return "".join(content)

def _format_quoted_material(quoted_material: Dict[str, Any], intro_content: str) -> str:
    """Format quoted legal material (statutes, case law, etc.)"""
    content = []
    
    # Introduction content before quote
    if intro_content:
        content.append(f"{intro_content}\n\n")
    
    # Quote source
    source = quoted_material.get("source", "")
    if source:
        content.append(f"> **{source}**\n>\n")
    
    # Main quoted content
    quote_content = quoted_material.get("content", "")
    if quote_content:
        # Format as blockquote
        quote_lines = quote_content.split('\n')
        for line in quote_lines:
            content.append(f"> {line}\n")
    
    # Internal paragraphs (like numbered subsections in statutes)
    internal_paras = quoted_material.get("internal_paragraphs", [])
    if internal_paras:
        content.append(">\n")
        for internal in internal_paras:
            identifier = internal.get("identifier", "")
            internal_content = internal.get("content", "")
            content.append(f"> {identifier} {internal_content}\n>\n")
    
    content.append("\n")
    return "".join(content)

def _format_subsections(subsections: List[Dict[str, Any]]) -> str:
    """Format subsections within paragraphs"""
    content = []
    
    for subsection in subsections:
        title = subsection.get("title", "")
        sub_content = subsection.get("content", "")
        
        if title:
            content.append(f"#### {title}\n")
        if sub_content:
            content.append(f"{sub_content}\n\n")
    
    return "".join(content)

def _process_footnote_references(text: str) -> str:
    """Process footnote references in text to maintain original positioning"""
    # This function keeps footnote references as they appear in the original text
    # The actual footnote content will be at the end of the document

    # Option 1: Superscript (traditional footnote style)
    text = re.sub(r'\[(\d+)\]', r'<sup>[\1]</sup>', text)

    return text

def _format_citations(citations: List[Dict[str, Any]]) -> str:
    """Format citations that appear in paragraphs"""
    if not citations:
        return ""
    
    citation_parts = []
    for citation in citations:
        cite_type = citation.get("type", "")
        reference = citation.get("reference", "")
        
        if cite_type and reference:
            citation_parts.append(f"Citation: {cite_type} - {reference}")
    
    if citation_parts:
        return f"*{'; '.join(citation_parts)}*\n\n"
    
    return ""

def _format_signatures(signatures: List[Dict[str, Any]]) -> str:
    """Format signatures section"""
    content = ["---\n\n"]
    
    for signature in signatures:
        name = signature.get("name", "")
        role = signature.get("role", "")
        date = signature.get("date", "")
        
        if date:
            content.append(f"**DATED** at Wellington this {date}\n\n")
            break  # Only show date once
    
    for signature in signatures:
        name = signature.get("name", "")
        role = signature.get("role", "")
        
        content.append(f"**{name}**  \n{role}\n\n")
    
    return "".join(content)

def _format_footnotes(footnotes: List[Dict[str, Any]]) -> str:
    """Format footnotes section"""
    content = ["---\n\n## Footnotes\n\n"]
    
    for footnote in footnotes:
        number = footnote.get("number", "")
        note_content = footnote.get("content", "")
        
        content.append(f"[^{number}]: {note_content}\n")
    
    content.append("\n")
    return "".join(content)

def save_markdown_file(json_data: Dict[str, Any], output_path: str) -> None:
    """
    Convert JSON to Markdown and save to file
    
    Args:
        json_data: Legal case JSON data
        output_path: Path where to save the markdown file
    """
    markdown_content = convert_legal_json_to_markdown(json_data)
    
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(markdown_content)
    
    print(f"Markdown file saved to: {output_path}")

# Process all JSON files in a directory
json_files = glob.glob("json_files/*.json")

for json_file in json_files:
    with open(json_file, "r") as f:
        case_data = json.load(f)
    
    # Create output filename
    base_name = os.path.splitext(os.path.basename(json_file))[0]
    output_file = f"markdown_output/{base_name}.md"
    
    # Convert and save
    save_markdown_file(case_data, output_file)