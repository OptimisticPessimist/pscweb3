/**
 * シーン番号を表示用にフォーマットする
 * @param actNumber 幕番号
 * @param sceneNumber シーン番号
 * @returns フォーマットされた文字列 (例: "1-1", "1", "Synopsis")
 */
export const formatSceneNumber = (actNumber: number | null | undefined, sceneNumber: number): string => {
    if (sceneNumber === 0) {
        return 'Synopsis'; // 既存のロジックでscene_number=0はあらすじとして扱われている場合が多い
    }
    
    if (actNumber) {
        return `${actNumber}-${sceneNumber}`;
    }
    
    return `${sceneNumber}`;
};
