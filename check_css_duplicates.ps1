# Script kiểm tra CSS trùng lặp
# Sử dụng: .\check_css_duplicates.ps1

Write-Host "=== KIỂM TRA CSS TRÙNG LẶP ===" -ForegroundColor Yellow

# Kiểm tra file mxh.css
Write-Host "`n1. Kiểm tra mxh.css:" -ForegroundColor Cyan
$mxhContent = Get-Content "app\static\css\mxh.css" -Raw
$selectors = [regex]::Matches($mxhContent, '([.#][\w-]+(?:\[[^\]]+\])?(?:\s*[.#][\w-]+)*)\s*{') | ForEach-Object { $_.Groups[1].Value.Trim() }

$duplicates = $selectors | Group-Object | Where-Object { $_.Count -gt 1 }
if ($duplicates) {
    Write-Host "❌ Tìm thấy trùng lặp:" -ForegroundColor Red
    $duplicates | ForEach-Object { Write-Host "  - $($_.Name): $($_.Count) lần" -ForegroundColor Red }
} else {
    Write-Host "✅ Không có trùng lặp" -ForegroundColor Green
}

# Kiểm tra file style.css
Write-Host "`n2. Kiểm tra style.css:" -ForegroundColor Cyan
$styleContent = Get-Content "app\static\css\style.css" -Raw
$styleSelectors = [regex]::Matches($styleContent, '([.#][\w-]+(?:\[[^\]]+\])?(?:\s*[.#][\w-]+)*)\s*{') | ForEach-Object { $_.Groups[1].Value.Trim() }

$styleDuplicates = $styleSelectors | Group-Object | Where-Object { $_.Count -gt 1 }
if ($styleDuplicates) {
    Write-Host "❌ Tìm thấy trùng lặp:" -ForegroundColor Red
    $styleDuplicates | ForEach-Object { Write-Host "  - $($_.Name): $($_.Count) lần" -ForegroundColor Red }
} else {
    Write-Host "✅ Không có trùng lặp" -ForegroundColor Green
}

Write-Host "`n=== HOÀN THÀNH KIỂM TRA ===" -ForegroundColor Yellow
