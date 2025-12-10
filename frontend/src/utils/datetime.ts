/**
 * 日時表示ユーティリティ
 * 
 * ISO 8601形式のUTC日時を、ブラウザのタイムゾーン（日本時間）でフォーマット
 */

/**
 * 日時をフル表示（年月日 時分秒）
 */
export const formatDateTime = (isoString: string): string => {
    const date = new Date(isoString);
    return date.toLocaleString('ja-JP', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
        timeZone: 'Asia/Tokyo'
    });
};

/**
 * 日時を表示（年月日 時分）
 */
export const formatDateTimeShort = (isoString: string): string => {
    const date = new Date(isoString);
    return date.toLocaleString('ja-JP', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
        timeZone: 'Asia/Tokyo'
    });
};

/**
 * 日付のみ表示（年月日）
 */
export const formatDate = (isoString: string): string => {
    const date = new Date(isoString);
    return date.toLocaleDateString('ja-JP', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        timeZone: 'Asia/Tokyo'
    });
};

/**
 * 時刻のみ表示（時分）
 */
export const formatTime = (isoString: string): string => {
    const date = new Date(isoString);
    return date.toLocaleTimeString('ja-JP', {
        hour: '2-digit',
        minute: '2-digit',
        timeZone: 'Asia/Tokyo'
    });
};

/**
 * 相対時刻表示（○分前、○時間前など）
 */
export const formatRelativeTime = (isoString: string): string => {
    const date = new Date(isoString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / (1000 * 60));
    const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));

    if (diffMins < 1) return 'たった今';
    if (diffMins < 60) return `${diffMins}分前`;
    if (diffHours < 24) return `${diffHours}時間前`;
    if (diffDays < 7) return `${diffDays}日前`;

    return formatDate(isoString);
};
