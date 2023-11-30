import React, { useState } from 'react';
import { Card, Form, Select, DatePicker, Button, Table, Typography, Space, message } from 'antd';
import { SearchOutlined, DownloadOutlined } from '@ant-design/icons';
import { apiService } from '../../services/apiService';

const { Title } = Typography;
const { RangePicker } = DatePicker;
const { Option } = Select;

const DataExplorer = () => {
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState([]);

  const onFinish = async (values) => {
    setLoading(true);
    try {
      const query = {
        equipment_ids: values.equipment_ids,
        sensor_types: values.sensor_types,
        start_time: values.dateRange?.[0]?.toISOString(),
        end_time: values.dateRange?.[1]?.toISOString(),
        aggregation: values.aggregation || 'raw'
      };
      
      const result = await apiService.queryData(query);
      setData(result.data);
      message.success(`Found ${result.count} data points`);
    } catch (error) {
      message.error('Failed to query data');
    } finally {
      setLoading(false);
    }
  };

  const handleExport = async () => {
    try {
      const values = form.getFieldsValue();
      const exportRequest = {
        equipment_ids: values.equipment_ids,
        sensor_types: values.sensor_types,
        start_time: values.dateRange?.[0]?.toISOString(),
        end_time: values.dateRange?.[1]?.toISOString(),
        format: 'csv'
      };
      
      const result = await apiService.exportData(exportRequest);
      message.success(`Export job created: ${result.job_id}`);
    } catch (error) {
      message.error('Failed to create export job');
    }
  };

  const columns = [
    {
      title: 'Equipment ID',
      dataIndex: 'equipment_id',
      key: 'equipment_id',
    },
    {
      title: 'Sensor Type',
      dataIndex: 'sensor_type',
      key: 'sensor_type',
    },
    {
      title: 'Value',
      dataIndex: 'value',
      key: 'value',
      render: (value) => typeof value === 'number' ? value.toFixed(2) : value,
    },
    {
      title: 'Timestamp',
      dataIndex: 'timestamp',
      key: 'timestamp',
      render: (timestamp) => new Date(timestamp).toLocaleString(),
    },
    {
      title: 'Quality',
      dataIndex: 'quality',
      key: 'quality',
    },
  ];

  return (
    <div style={{ padding: '24px' }}>
      <Title level={2}>Data Explorer</Title>
      
      <Card title="Query Data" style={{ marginBottom: '24px' }}>
        <Form
          form={form}
          layout="vertical"
          onFinish={onFinish}
        >
          <Space wrap>
            <Form.Item name="equipment_ids" label="Equipment IDs">
              <Select
                mode="multiple"
                placeholder="Select equipment"
                style={{ minWidth: 200 }}
              >
                <Option value="pump-001">Pump 001</Option>
                <Option value="motor-002">Motor 002</Option>
                <Option value="sensor-003">Sensor 003</Option>
              </Select>
            </Form.Item>
            
            <Form.Item name="sensor_types" label="Sensor Types">
              <Select
                mode="multiple"
                placeholder="Select sensor types"
                style={{ minWidth: 200 }}
              >
                <Option value="temperature">Temperature</Option>
                <Option value="pressure">Pressure</Option>
                <Option value="vibration">Vibration</Option>
              </Select>
            </Form.Item>
            
            <Form.Item name="dateRange" label="Date Range">
              <RangePicker showTime />
            </Form.Item>
            
            <Form.Item name="aggregation" label="Aggregation">
              <Select defaultValue="raw" style={{ width: 120 }}>
                <Option value="raw">Raw</Option>
                <Option value="avg">Average</Option>
                <Option value="min">Minimum</Option>
                <Option value="max">Maximum</Option>
              </Select>
            </Form.Item>
          </Space>
          
          <div style={{ marginTop: '16px' }}>
            <Space>
              <Button 
                type="primary" 
                htmlType="submit" 
                icon={<SearchOutlined />}
                loading={loading}
              >
                Query Data
              </Button>
              <Button 
                icon={<DownloadOutlined />}
                onClick={handleExport}
              >
                Export Data
              </Button>
            </Space>
          </div>
        </Form>
      </Card>

      <Card title="Query Results">
        <Table
          columns={columns}
          dataSource={data}
          loading={loading}
          pagination={{ pageSize: 50 }}
          scroll={{ x: 800 }}
        />
      </Card>
    </div>
  );
};

export default DataExplorer;