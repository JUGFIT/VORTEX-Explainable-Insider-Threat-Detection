import React from 'react';
import Layout from '../components/Layout/Layout';
import SimulationPanel from '../components/Simulation/SimulationPanel';

const Demo = () => {
    return (
        <Layout title="Event Log Generator" hideSidebar={true}>
            <div className="h-full pb-8">
                <SimulationPanel
                    isOpen={true}
                    inline={true}
                    onShowReveal={() => {
                        window.dispatchEvent(new Event('refreshDashboard'));
                    }}
                />
            </div>
        </Layout>
    );
};

export default Demo;
