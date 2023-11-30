import React from 'react';
import { Layout, Typography, Space, Badge, Avatar } from 'antd';
import { BellOutlined, UserOutlined } from '@ant-design/icons';
import styled from 'styled-components';

const { Header: AntHeader } = Layout;
const { Title } = Typography;

const StyledHeader = styled(AntHeader)`
  background: #fff;
  padding: 0 24px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  box-shadow: 0 1px 4px rgba(0,21,41,.08);
  position: sticky;
  top: 0;
  z-index: 10;
`;

const HeaderTitle = styled(Title)`
  margin: 0 !important;
  color: #001529 !important;
  font-size: 20px !important;
`;

const HeaderActions = styled(Space)`
  align-items: center;
`;

const Header = ({ title }) => {
  return (
    <StyledHeader>
      <HeaderTitle level={3}>{title}</HeaderTitle>
      <HeaderActions size="large">
        <Badge count={3} size="small">
          <BellOutlined style={{ fontSize: '18px', color: '#666' }} />
        </Badge>
        <Avatar icon={<UserOutlined />} />
      </HeaderActions>
    </StyledHeader>
  );
};

export default Header;