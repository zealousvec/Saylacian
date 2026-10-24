param(
    [Parameter(Mandatory=$true)][ValidateSet('latin','image','saylacian')][string]$Mode,
    [Parameter(Mandatory=$true)][string]$EvidencePath,
    [string]$ImagePath
)

Add-Type -AssemblyName System.Windows.Forms
$data = [System.Windows.Forms.Clipboard]::GetDataObject()
if ($null -eq $data) { throw 'Windows clipboard is empty.' }
$formats = @($data.GetFormats($false))
$result = [ordered]@{ mode = $Mode; formats = $formats }

switch ($Mode) {
    'latin' {
        $text = [System.Windows.Forms.Clipboard]::GetText(
            [System.Windows.Forms.TextDataFormat]::UnicodeText
        )
        if ($text -ne 'hello, what is wrong with you,') { throw "Unexpected Unicode text: $text" }
        $result.text = $text
        $result.pass = $true
    }
    'image' {
        if (-not [System.Windows.Forms.Clipboard]::ContainsImage()) {
            throw 'External WinForms reader did not recognize the CF_DIB image.'
        }
        $image = [System.Windows.Forms.Clipboard]::GetImage()
        if ($image.Width -lt 500 -or $image.Height -lt 100) { throw 'Clipboard image dimensions are invalid.' }
        $image.Save($ImagePath, [System.Drawing.Imaging.ImageFormat]::Png)
        $result.width = $image.Width
        $result.height = $image.Height
        $result.image_saved = $ImagePath
        $result.pass = $true
    }
    'saylacian' {
        $names = @($formats)
        foreach ($required in @('Saylacian Text v1', 'Rich Text Format', 'HTML Format', 'UnicodeText')) {
            if ($names -notcontains $required) { throw "Clipboard missing format: $required" }
        }
        $plain = [System.Windows.Forms.Clipboard]::GetText(
            [System.Windows.Forms.TextDataFormat]::UnicodeText
        )
        if (-not $plain.StartsWith("SAYLACIAN-TEXT/1`n")) { throw 'Unicode fallback lacks Saylacian Text header.' }
        if (-not $data.GetDataPresent('Rich Text Format', $false)) { throw 'WinForms cannot retrieve RTF.' }
        if (-not $data.GetDataPresent('HTML Format', $false)) { throw 'WinForms cannot retrieve HTML.' }
        $rtf = $data.GetData('Rich Text Format', $false)
        $html = $data.GetData('HTML Format', $false)
        $result.plain_header = ($plain -split "`n", 2)[0]
        $result.unicode_fallback = $plain
        $result.rtf_type = $rtf.GetType().FullName
        $result.html_type = $html.GetType().FullName
        $result.pass = $true
    }
}

$result | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath $EvidencePath -Encoding utf8
