# PowerShell script to create extension icons
$icon16 = @"
<svg width="16" height="16" xmlns="http://www.w3.org/2000/svg">
  <rect width="16" height="16" fill="#4285F4" rx="2" ry="2"/>
  <path d="M4 4 L12 4 L12 6 L4 6 Z" fill="white"/>
  <path d="M4 8 L12 8 L12 10 L4 10 Z" fill="white"/>
  <path d="M4 12 L8 12 L8 14 L4 14 Z" fill="white"/>
</svg>
"@

$icon48 = @"
<svg width="48" height="48" xmlns="http://www.w3.org/2000/svg">
  <rect width="48" height="48" fill="#4285F4" rx="6" ry="6"/>
  <path d="M12 12 L36 12 L36 18 L12 18 Z" fill="white"/>
  <path d="M12 24 L36 24 L36 30 L12 30 Z" fill="white"/>
  <path d="M12 36 L24 36 L24 42 L12 42 Z" fill="white"/>
</svg>
"@

$icon128 = @"
<svg width="128" height="128" xmlns="http://www.w3.org/2000/svg">
  <rect width="128" height="128" fill="#4285F4" rx="16" ry="16"/>
  <path d="M32 32 L96 32 L96 48 L32 48 Z" fill="white"/>
  <path d="M32 64 L96 64 L96 80 L32 80 Z" fill="white"/>
  <path d="M32 96 L64 96 L64 112 L32 112 Z" fill="white"/>
</svg>
"@

# Save SVGs to temporary files
$icon16 | Out-File -FilePath "$PSScriptRoot\temp_icon16.svg" -Encoding UTF8
$icon48 | Out-File -FilePath "$PSScriptRoot\temp_icon48.svg" -Encoding UTF8
$icon128 | Out-File -FilePath "$PSScriptRoot\temp_icon128.svg" -Encoding UTF8

Write-Host "SVG files created. Now you need to convert them to PNG format using a tool like Inkscape, ImageMagick, or an online converter."
Write-Host "After conversion, remember to name them as: icon16.png, icon48.png, and icon128.png"
