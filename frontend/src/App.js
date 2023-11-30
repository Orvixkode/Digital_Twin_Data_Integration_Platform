import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { Layout, ConfigProvider, theme } from 'antd';
import { DashboardOutlined, SettingOutlined, DatabaseOutlined, MonitorOutlined } from '@ant-design/icons';

import Sidebar from './components/layout/Sidebar';
import Header from './components/layout/Header';
import Dashboard from './components/dashboard/Dashboard';
import EquipmentMonitoring from './components/monitoring/EquipmentMonitoring';
import DataExplorer from './components/data/DataExplorer';
import SystemSettings from './components/settings/SystemSettings';

import './App.css';

const { Content } = Layout;

const menuItems = [
  {
    key: 'dashboard',
    icon: <DashboardOutlined />,
    label: 'Dashboard',
    path: '/'
  },
  {
    key: 'monitoring',
    icon: <MonitorOutlined />,
    label: 'Equipment Monitoring',
    path: '/monitoring'
  },
  {
    key: 'data',
    icon: <DatabaseOutlined />,
    label: 'Data Explorer',
    path: '/data'
  },
  {
    key: 'settings',
    icon: <SettingOutlined />,
    label: 'System Settings',
    path: '/settings'
  }
];

function App() {
  return (
    <ConfigProvider
      theme={{
        algorithm: theme.defaultAlgorithm,
        token: {
          colorPrimary: '#1890ff',
          colorBgContainer: '#ffffff',
        },
      }}
    >
      <Router>
        <Layout className="app-layout">
          <Sidebar menuItems={menuItems} />
          <Layout className="main-layout">
            <Header title="Digital Twin Data Integration Platform" />
            <Content className="app-content">
              <Routes>
                <Route path="/" element={<Dashboard />} />
                <Route path="/monitoring" element={<EquipmentMonitoring />} />
                <Route path="/data" element={<DataExplorer />} />
                <Route path="/settings" element={<SystemSettings />} />
              </Routes>
            </Content>
          </Layout>
        </Layout>
      </Router>
    </ConfigProvider>
  );
}

export default App;