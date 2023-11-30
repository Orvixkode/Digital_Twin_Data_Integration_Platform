import React, { useState, useEffect } from 'react';
import { Card, Table, Tag, Space, Typography, Row, Col } from 'antd';
import { CheckCircleOutlined, ExclamationCircleOutlined, CloseCircleOutlined } from '@ant-design/icons';
import { apiService } from '../../services/apiService';

const { Title } = Typography;

const EquipmentMonitoring = () => {
  const [equipmentHealth, setEquipmentHealth] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchEquipmentHealth();
    const interval = setInterval(fetchEquipmentHealth, 10000); // Update every 10 seconds
    return () => clearInterval(interval);
  }, []);

  const fetchEquipmentHealth = async () => {
    try {
      const data = await apiService.getEquipmentHealth();
      setEquipmentHealth(data.equipment);
      setLoading(false);
    } catch (error) {
      console.error('Error fetching equipment health:', error);
      setLoading(false);
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'HEALTHY':
        return <CheckCircleOutlined style={{ color: '#52c41a' }} />;
      case 'DEGRADED':
        return <ExclamationCircleOutlined style={{ color: '#fa8c16' }} />;
      case 'OFFLINE':
        return <CloseCircleOutlined style={{ color: '#ff4d4f' }} />;
      default:
        return <ExclamationCircleOutlined style={{ color: '#d9d9d9' }} />;
    }
  };

  const columns = [
    {
      title: 'Equipment ID',
      dataIndex: 'equipment_id',
      key: 'equipment_id',
    },
    {
      title: 'Name',
      dataIndex: 'name',
      key: 'name',
    },
    {
      title: 'Type',
      dataIndex: 'type',
      key: 'type',
    },
    {
      title: 'Protocol',
      dataIndex: 'protocol',
      key: 'protocol',
      render: (protocol) => <Tag color="blue">{protocol}</Tag>,
    },
    {
      title: 'Health Status',
      dataIndex: 'health_status',
      key: 'health_status',
      render: (status) => (
        <Space>
          {getStatusIcon(status)}
          <span>{status}</span>
        </Space>
      ),
    },
    {
      title: 'Data Quality',
      dataIndex: 'data_quality',
      key: 'data_quality',
      render: (quality) => {
        const color = quality === 'EXCELLENT' ? 'green' : quality === 'GOOD' ? 'blue' : 'orange';
        return <Tag color={color}>{quality}</Tag>;
      },
    },
    {
      title: 'Recent Data Points',
      dataIndex: 'recent_data_points',
      key: 'recent_data_points',
    },
  ];

  return (
    <div style={{ padding: '24px' }}>
      <Title level={2}>Equipment Monitoring</Title>
      
      <Card title="Equipment Health Overview" loading={loading}>
        <Table
          columns={columns}
          dataSource={equipmentHealth}
          rowKey="equipment_id"
          pagination={{ pageSize: 10 }}
          scroll={{ x: 800 }}
        />
      </Card>
    </div>
  );
};

export default EquipmentMonitoring;