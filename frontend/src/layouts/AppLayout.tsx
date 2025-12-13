import { useState } from 'react';
import { Outlet } from 'react-router-dom';
import { Sidebar } from '../components/layout/Sidebar';
import { Header } from '../components/layout/Header';

export function AppLayout() {
    const [sidebarOpen, setSidebarOpen] = useState(false);

    return (
        <div className="flex h-screen bg-gray-50">
            <Sidebar isOpen={sidebarOpen} onClose={() => setSidebarOpen(false)} />

            <div className="flex-1 flex flex-col min-w-0 overflow-hidden h-full">
                <Header onMenuClick={() => setSidebarOpen(true)} />

                <main className="flex-1 overflow-auto p-6 scroll-smooth">
                    <div className="max-w-7xl mx-auto w-full h-full flex flex-col">
                        <Outlet />
                    </div>
                </main>
            </div>
        </div>
    );
}
