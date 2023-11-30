import React from 'react';
import { Card, Typography, Descriptions, Tag, Space } from 'antd';

const { Title } = Typography;

const SystemSettings = () => {
  return (
    <div style={{ padding: '24px' }}>
      <Title level={2}>System Settings</Title>
      
      <Card title="Platform Configuration" style={{ marginBottom: '24px' }}>
        <Descriptions bordered column={2}>
          <Descriptions.Item label="Platform Version">1.0.0</Descriptions.Item>
          <Descriptions.Item label="API Version">v1</Descriptions.Item>
          <Descriptions.Item label="Max Equipment Connections">15</Descriptions.Item>
          <Descriptions.Item label="Data Retention">90 days</Descriptions.Item>
          <Descriptions.Item label="Processing Interval">30 seconds</Descriptions.Item>
          <Descriptions.Item label="Rate Limit">100 req/min</Descriptions.Item>
        </Descriptions>
      </Card>

      <Card title="Protocol Configuration">
        <Space direction="vertical" style={{ width: '100%' }}>
          <Card size="small" title="MQTT Configuration">
            <Descriptions size="small" column={1}>
              <Descriptions.Item label="Broker">localhost:1883</Descriptions.Item>
              <Descriptions.Item label="QoS Level">1</Descriptions.Item>
              <Descriptions.Item label="Keep Alive">60 seconds</Descriptions.Item>
              <Descriptions.Item label="Status">
                <Tag color="green">Connected</Tag>
              </Descriptions.Item>
            </Descriptions>
          </Card>

          <Card size="small" title="OPC UA Configuration">
            <Descriptions size="small" column={1}>
              <Descriptions.Item label="Endpoint">opc.tcp://localhost:4840/freeopcua/server/</Descriptions.Item>
              <Descriptions.Item label="Security Policy">None</Descriptions.Item>
              <Descriptions.Item label="Connection Timeout">30 seconds</Descriptions.Item>
              <Descriptions.Item label="Status">
                <Tag color="green">Connected</Tag>
              </Descriptions.Item>
            </Descriptions>
          </Card>
        </Space>
      </Card>
    </div>
  );
};

export default SystemSettings;