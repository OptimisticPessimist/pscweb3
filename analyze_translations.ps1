# 残りページの効率的な翻訳対応スクリプト

# 翻訳が必要な主要コンポーネントのリスト
$componentsToTranslate = @(
    "features/projects/ProjectDetailsPage.tsx",
    "features/schedule/pages/SchedulePage.tsx",
    "features/casting/pages/CastingPage.tsx",
    "features/staff/pages/StaffPage.tsx",
    "features/attendance/AttendancePage.tsx",
    "features/scene_charts/pages/SceneChartPage.tsx"
)

Write-Host "残りの翻訳対象コンポーネント："
foreach ($component in $componentsToTranslate) {
    $fullPath = "frontend/src/$component"
    if (Test-Path $fullPath) {
        Write-Host "  ✓ $component"
        
        # ハードコードされた英語テキストを検出
        $content = Get-Content $fullPath -Raw
        $matches = [regex]::Matches($content, '(?<=>)([A-Z][a-zA-Z ]{3,}?)(?=<)')
        
        if ($matches.Count -gt 0) {
            Write-Host "    検出されたテキスト: $($matches.Count)個"
            $matches | Select-Object -First 3 | ForEach-Object {
                Write-Host "      - $($_.Value)"
            }
        }
    }
    else {
        Write-Host "  ✗ $component (not found)"
    }
}

Write-Host "`n次のステップ:"
Write-Host "1. 主要ページのテキストパターンを特定"
Write-Host "2. 共通翻訳キーを翻訳ファイルに追加"  
Write-Host "3. 各ページにuseTranslationを追加して翻訳キーに置き換え"
