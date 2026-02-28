import React from 'react';
import Sidebar from './Sidebar';
import Header from './Header';

const Layout = ({ children, title, subtitle, hideSidebar = false }) => {
    return (
        <div className="h-screen bg-vortex-darker flex overflow-hidden">
            {!hideSidebar && <Sidebar />}
            <div className={`flex-1 flex flex-col min-w-0 ${!hideSidebar ? 'ml-64' : ''}`}>
                <Header title={title} subtitle={subtitle} />
                <main className={`flex-1 overflow-y-auto ${hideSidebar ? '' : 'p-8'} custom-scrollbar`}>
                    {children}
                </main>
            </div>
        </div>
    );
};

export default Layout;
