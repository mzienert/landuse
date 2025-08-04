export interface FormattedTextSection {
  type: 'heading' | 'section' | 'paragraph' | 'list-item' | 'metadata';
  content: string;
  level?: number;
}

export function parseAndFormatText(text: string): FormattedTextSection[] {
  const lines = text.split('\n').filter(line => line.trim());
  const sections: FormattedTextSection[] = [];
  let currentParagraph: string[] = [];

  const flushParagraph = () => {
    if (currentParagraph.length > 0) {
      sections.push({
        type: 'paragraph',
        content: currentParagraph.join(' ')
      });
      currentParagraph = [];
    }
  };

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i].trim();
    
    if (!line) continue;

    // Chapter/Article headings (all caps, contains "Chapter" or "Article")
    if (line.includes('Chapter') && line === line.toUpperCase()) {
      flushParagraph();
      sections.push({
        type: 'heading',
        content: line,
        level: 1
      });
    }
    // Article headings
    else if (line.includes('Article') && line === line.toUpperCase()) {
      flushParagraph();
      sections.push({
        type: 'heading',
        content: line,
        level: 2
      });
    }
    // Section numbers (Sec. X-XX.)
    else if (/^Sec\.\s+\d+[-\d]*\.?$/.test(line)) {
      flushParagraph();
      sections.push({
        type: 'section',
        content: line
      });
    }
    // Subsection numbers (like "105.3 Application for permit.")
    else if (/^\d+\.\d+\s+/.test(line)) {
      flushParagraph();
      sections.push({
        type: 'section',
        content: line
      });
    }
    // Metadata (parentheses with resolution info or effective dates)
    else if (line.startsWith('(') && line.endsWith(')')) {
      flushParagraph();
      sections.push({
        type: 'metadata',
        content: line
      });
    }
    // Effective dates
    else if (line.startsWith('Effective on:')) {
      flushParagraph();
      sections.push({
        type: 'metadata',
        content: line
      });
    }
    // List items (start with numbers, letters, or bullets)
    else if (/^[\d]+\.\s/.test(line) || line.startsWith('•') || line.startsWith('-')) {
      flushParagraph();
      sections.push({
        type: 'list-item',
        content: line
      });
    }
    // Continue building paragraph - collect lines that should flow together
    else {
      currentParagraph.push(line);
    }
  }

  // Flush any remaining paragraph
  flushParagraph();

  return sections;
}

export function formatTextForDisplay(text: string, maxLength?: number): string {
  // If no max length specified, return formatted version
  if (!maxLength) {
    return text.replace(/\n/g, '\n').trim();
  }

  // For truncated text, try to break at a natural point
  if (text.length <= maxLength) {
    return text.replace(/\n/g, '\n').trim();
  }

  const truncated = text.substring(0, maxLength);
  
  // Try to break at the end of a sentence
  const lastSentence = truncated.lastIndexOf('.');
  if (lastSentence > maxLength * 0.7) {
    return truncated.substring(0, lastSentence + 1).replace(/\n/g, '\n').trim();
  }

  // Try to break at the end of a line
  const lastNewline = truncated.lastIndexOf('\n');
  if (lastNewline > maxLength * 0.7) {
    return truncated.substring(0, lastNewline).replace(/\n/g, '\n').trim();
  }

  // Fall back to word boundary
  const lastSpace = truncated.lastIndexOf(' ');
  if (lastSpace > maxLength * 0.8) {
    return truncated.substring(0, lastSpace).replace(/\n/g, '\n').trim();
  }

  return truncated.replace(/\n/g, '\n').trim();
}