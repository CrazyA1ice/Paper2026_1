$ErrorActionPreference='Stop'
$qaV75Directory='C:\Users\Quant\Desktop\Paper2026_1\review_scratch\v75_high_priority_20261008'
$qaV75Source='C:\Users\Quant\Desktop\Paper2026_1\word_output\2026.10.08v75.docx'
$qaV75Copy=Join-Path $qaV75Directory 'render_v75_readonly.docx'
Copy-Item -LiteralPath $qaV75Source -Destination $qaV75Copy
$qaV75Word=$null
$qaV75Document=$null
try {
 $qaV75Word=New-Object -ComObject Word.Application
 $qaV75Word.Visible=$false
 $qaV75Word.DisplayAlerts=0
 $qaV75Document=$qaV75Word.Documents.Open($qaV75Copy,$false,$true,$false)
 $qaV75Document.ExportAsFixedFormat((Join-Path $qaV75Directory 'v75_review.pdf'),17)
 $qaV75Stats=[ordered]@{words=$qaV75Document.ComputeStatistics(0,$false);characters=$qaV75Document.ComputeStatistics(3,$false);pages=$qaV75Document.ComputeStatistics(2,$false)}
 $qaV75Fonts=foreach($qaIndex in @(1,2,3,4,12,23,50)){ $qaReadRange=$qaV75Document.Paragraphs.Item($qaIndex).Range; [ordered]@{paragraph=$qaIndex;size=$qaReadRange.Font.Size;chinese=$qaReadRange.Font.NameFarEast;latin=$qaReadRange.Font.NameAscii;line_spacing_rule=$qaReadRange.ParagraphFormat.LineSpacingRule;line_spacing=$qaReadRange.ParagraphFormat.LineSpacing} }
 @{statistics=$qaV75Stats;font_examples=@($qaV75Fonts)} | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath (Join-Path $qaV75Directory 'word_actual_properties.json') -Encoding utf8
 'Export and format inspection complete'
} finally {
 if($null -ne $qaV75Document){try{$qaV75Document.Close(0)}catch{}}
 if($null -ne $qaV75Word){try{if($qaV75Word.Documents.Count -eq 0){$qaV75Word.Quit(0)}}catch{}}
}
