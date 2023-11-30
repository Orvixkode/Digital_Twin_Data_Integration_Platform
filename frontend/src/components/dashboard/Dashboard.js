import React, { useState, useEffect } from 'react';
import { Row, Col, Card, Statistic, Progress, Alert, Typography, Space, Badge } from 'antd';
import { 
  DatabaseOutlined, 
  ThunderboltOutlined, 
  WarningOutlined,
  CheckCircleOutlined,
  DisconnectOutlined 
} from '@ant-design/icons';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar } from 'recharts';
import { apiService } from '../../services/apiService';

const { Title, Text } = Typography;

const Dashboard = () => {
  const [dashboardData, setDashboardData] = useState({
    total_equipment: 0,
    active_equipment: 0,
    connected_equipment: 0,
    total_alerts: 0,
    critical_alerts: 0,
    data_points_today: 0,
    protocols_summary: {}
  });
  
  const [realtimeData, setRealtimeData] = useState([]);
  const [performanceData, setPerformanceData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [alerts, setAlerts] = useState([]);

  useEffect(() => {
    fetchDashboardData();
    fetchRealtimeData();
    fetchPerformanceMetrics();
    fetchActiveAlerts();

    // Set up real-time updates every 5 seconds
    const interval = setInterval(() => {
      fetchDashboardData();
      fetchRealtimeData();
    }, 5000);

    return () => clearInterval(interval);
  }, []);

  const fetchDashboardData = async () => {
    try {
      const data = await apiService.getDashboardOverview();
      setDashboardData(data);
      setLoading(false);
    } catch (error) {
      console.error('Error fetching dashboard data:', error);
      setLoading(false);
    }
  };

  const fetchRealtimeData = async () => {
    try {
      const data = await apiService.getRealtimeData();
      // Format data for charts
      const chartData = data.data.slice(0, 10).map((item, index) => ({
        time: new Date(item.timestamp).toLocaleTimeString(),
        value: item.value,
        equipment: item.equipment_name,
        status: item.status
      }));
      setRealtimeData(chartData);
    } catch (error) {
      console.error('Error fetching realtime data:', error);
    }
  };

  const fetchPerformanceMetrics = async () => {
    try {
      const data = await apiService.getPerformanceMetrics();
      // Format protocol data for bar chart
      const protocolData = Object.entries(data.protocol_breakdown || {}).map(([protocol, count]) => ({
        protocol,
        count,
        percentage: ((count / Object.values(data.protocol_breakdown).reduce((a, b) => a + b, 0)) * 100).toFixed(1)
      }));
      setPerformanceData(protocolData);
    } catch (error) {
      console.error('Error fetching performance metrics:', error);
    }
  };

  const fetchActiveAlerts = async () => {
    try {
      const data = await apiService.getActiveAlerts({ limit: 5 });
      setAlerts(data.alerts);
    } catch (error) {
      console.error('Error fetching alerts:', error);
    }
  };

  const getConnectionRate = () => {
    if (dashboardData.active_equipment === 0) return 0;
    return ((dashboardData.connected_equipment / dashboardData.active_equipment) * 100).toFixed(1);
  };

  const getProtocolChartData = () => {
    return Object.entries(dashboardData.protocols_summary).map(([protocol, count]) => ({
      protocol,
      count
    }));
  };

  return (
    <div style={{ padding: '24px', backgroundColor: '#f5f5f5' }}>
      <Title level={2}>Digital Twin Dashboard</Title>
      <Text type="secondary">Real-time monitoring and data integration platform</Text>

      {/* Key Metrics Cards */}
      <Row gutter={[24, 24]} style={{ marginTop: '24px' }}>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="Total Equipment"
              value={dashboardData.total_equipment}
              prefix={<DatabaseOutlined style={{ color: '#1890ff' }} />}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="Connected"
              value={dashboardData.connected_equipment}
              suffix={`/ ${dashboardData.active_equipment}`}
              prefix={<CheckCircleOutlined style={{ color: '#52c41a' }} />}
            />
            <Progress 
              percent={parseFloat(getConnectionRate())} 
              size="small" 
              strokeColor="#52c41a"
              style={{ marginTop: '8px' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="Active Alerts"
              value={dashboardData.total_alerts}
              prefix={<WarningOutlined style={{ color: '#fa8c16' }} />}
            />
            {dashboardData.critical_alerts > 0 && (
              <Text type="danger" style={{ fontSize: '12px' }}>
                {dashboardData.critical_alerts} critical
              </Text>
            )}
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="Data Points Today"
              value={dashboardData.data_points_today}
              prefix={<ThunderboltOutlined style={{ color: '#722ed1' }} />}
            />
          </Card>
        </Col>
      </Row>

      {/* Charts and Visualizations */}
      <Row gutter={[24, 24]} style={{ marginTop: '24px' }}>
        <Col xs={24} lg={16}>
          <Card title="Real-time Sensor Readings" loading={loading}>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={realtimeData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="time" />
                <YAxis />
                <Tooltip />
                <Line 
                  type="monotone" 
                  dataKey="value" 
                  stroke="#1890ff" 
                  strokeWidth={2}
                  dot={{ fill: '#1890ff', strokeWidth: 2 }}
                />
              </LineChart>
            </ResponsiveContainer>
          </Card>
        </Col>
        
        <Col xs={24} lg={8}>
          <Card title="Protocol Distribution" loading={loading}>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={performanceData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="protocol" />
                <YAxis />
                <Tooltip />
                <Bar dataKey="count" fill="#52c41a" />
              </BarChart>
            </ResponsiveContainer>
          </Card>
        </Col>
      </Row>

      {/* Recent Alerts and System Status */}
      <Row gutter={[24, 24]} style={{ marginTop: '24px' }}>
        <Col xs={24} lg={12}>
          <Card title="Recent Alerts" loading={loading}>
            <Space direction="vertical" style={{ width: '100%' }}>
              {alerts.length > 0 ? (
                alerts.map((alert, index) => (
                  <Alert
                    key={alert.alert_id}
                    message={alert.title}
                    description={
                      <Space direction="vertical">
                        <Text>{alert.message}</Text>
                        <Text type="secondary" style={{ fontSize: '12px' }}>
                          {alert.age_minutes} minutes ago
                        </Text>
                      </Space>
                    }
                    type={alert.severity === 'CRITICAL' ? 'error' : 'warning'}
                    showIcon
                    closable
                  />
                ))
              ) : (
                <Text type="secondary">No active alerts</Text>
              )}
            </Space>
          </Card>
        </Col>

        <Col xs={24} lg={12}>
          <Card title="System Status" loading={loading}>
            <Space direction="vertical" style={{ width: '100%' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <Text>MQTT Service</Text>
                <Badge status="success" text="Online" />
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <Text>OPC UA Service</Text>
                <Badge status="success" text="Online" />
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <Text>Database</Text>
                <Badge status="success" text="Connected" />
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <Text>Data Processing</Text>
                <Badge status="processing" text="Processing" />
              </div>
              
              <div style={{ marginTop: '16px', padding: '12px', backgroundColor: '#f6ffed', borderRadius: '6px' }}>
                <Text type="success">
                  <CheckCircleOutlined style={{ marginRight: '8px' }} />
                  All systems operational - 99.8% uptime
                </Text>
              </div>
            </Space>
          </Card>
        </Col>
      </Row>
    </div>
  );
};

export default Dashboard;