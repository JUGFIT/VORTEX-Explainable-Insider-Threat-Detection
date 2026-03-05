import React from 'react';
import Sidebar from './Sidebar';
import Header from './Header';

const Layout = ({ children, title, subtitle }) => {
    return (
        <div className="min-h-screen bg-vortex-darker">
            <Sidebar />
            <div className="ml-64">
                <Header title={title} subtitle={subtitle} />
                <main className="p-8">
                    {children}
                </main>
            </div>
        </div>
    );
};

export default Layout;
