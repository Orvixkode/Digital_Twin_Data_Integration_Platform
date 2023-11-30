import React, { useState } from 'react';
import { Layout, Menu } from 'antd';
import { useNavigate, useLocation } from 'react-router-dom';
import styled from 'styled-components';

const { Sider } = Layout;

const StyledSider = styled(Sider)`
  .ant-layout-sider-trigger {
    background: #002140;
  }
  
  .ant-menu-dark {
    background: #001529;
  }
  
  .ant-menu-dark .ant-menu-item-selected {
    background: #1890ff;
  }
`;

const Logo = styled.div`
  height: 64px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #002140;
  color: white;
  font-size: 16px;
  font-weight: bold;
  margin: 0;
  text-align: center;
  line-height: 1.2;
`;

const Sidebar = ({ menuItems }) => {
  const [collapsed, setCollapsed] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();

  const getSelectedKey = () => {
    const currentPath = location.pathname;
    const item = menuItems.find(item => item.path === currentPath);
    return item ? item.key : 'dashboard';
  };

  const handleMenuClick = ({ key }) => {
    const item = menuItems.find(item => item.key === key);
    if (item) {
      navigate(item.path);
    }
  };

  return (
    <StyledSider
      collapsible
      collapsed={collapsed}
      onCollapse={(value) => setCollapsed(value)}
      theme="dark"
      width={240}
      collapsedWidth={80}
    >
      <Logo>
        {collapsed ? 'DT' : 'Digital Twin'}
      </Logo>
      <Menu
        theme="dark"
        mode="inline"
        selectedKeys={[getSelectedKey()]}
        onClick={handleMenuClick}
        style={{ borderRight: 0 }}
      >
        {menuItems.map(item => (
          <Menu.Item key={item.key} icon={item.icon}>
            {item.label}
          </Menu.Item>
        ))}
      </Menu>
    </StyledSider>
  );
};

export default Sidebar;