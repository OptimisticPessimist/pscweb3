# Backend API error messages translation mapping
$translations = @{
    "認証が必要です" = "Authentication required"
    "無効なトークンです" = "Invalid token"
    "プロジェクトが見つかりません" = "Project not found"
    "脚本が見つかりません" = "Script not found"
    "このプロジェクトへのアクセス権がありません" = "Access denied to this project"
    "香盤表が見つかりません" = "Scene chart not found"
    "スケジュール作成の権限がありません" = "Permission denied to create schedule"
    "稽古スケジュールが見つかりません" = "Rehearsal schedule not found"
    "スケジュールが見つかりません" = "Schedule not found"
    "稽古追加の権限がありません" = "Permission denied to add rehearsal"
    "稽古が見つかりません" = "Rehearsal not found"
    "稽古更新の権限がありません" = "Permission denied to update rehearsal"
    "稽古削除の権限がありません" = "Permission denied to delete rehearsal"
    "参加者が見つかりません" = "Participant not found"
    "変更権限がありません" = "Permission denied to modify"
    "削除権限がありません" = "Permission denied to delete"
    "キャスト割り当てが見つかりません" = "Cast assignment not found"
    "自分自身のロールは変更できません" = "Cannot change your own role"
    "メンバーが見つかりません" = "Member not found"
    "権限がありません" = "Permission denied"
    "オーナーは脱退できません。プロジェクトを削除するか、オーナー権限を委譲してください" = "Owner cannot leave. Delete the project or transfer ownership"
    "招待トークンが無効または期限切れです" = "Invalid or expired invitation token"
    "既にプロジェクトのメンバーです" = "Already a member of this project"
    "配役が見つかりません" = "Cast not found"
    "配役を削除する権限がありません" = "Permission denied to delete cast"
    "登場人物が見つかりません" = "Character not found"
    "削除する権限がありません" = "Permission denied to delete"
}

# Get all Python files in src/api directory
$files = Get-ChildItem -Path "backend/src/api" -Filter "*.py" -Recurse

foreach ($file in $files) {
    $content = Get-Content $file.FullName -Raw -Encoding UTF8
    $modified = $false
    
    foreach ($jp in $translations.Keys) {
        $en = $translations[$jp]
        if ($content -match [regex]::Escape($jp)) {
            $content = $content -replace [regex]::Escape($jp), $en
            $modified = $true
            Write-Host "Translated '$jp' -> '$en' in $($file.Name)"
        }
    }
    
    if ($modified) {
        Set-Content -Path $file.FullName -Value $content -Encoding UTF8 -NoNewline
        Write-Host "Updated: $($file.FullName)"
    }
}

Write-Host "Translation complete!"
