import React from 'react';

export const Loading: React.FC = () => {
    return (
        <div className="flex justify-center items-center h-full min-h-[200px]">
            <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-indigo-600"></div>
        </div>
    );
};
