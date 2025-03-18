// main.dart
import 'package:flutter/material.dart';
import 'package:pubnub/pubnub.dart';
import 'package:flutter_local_notifications/flutter_local_notifications.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await initNotifications();
  runApp(MyApp());
}

// 初始化本地通知
final FlutterLocalNotificationsPlugin flutterLocalNotificationsPlugin =
    FlutterLocalNotificationsPlugin();

Future<void> initNotifications() async {
  const AndroidInitializationSettings initializationSettingsAndroid =
      AndroidInitializationSettings('@mipmap/ic_launcher');
  
  final DarwinInitializationSettings initializationSettingsIOS =
      DarwinInitializationSettings(
    requestAlertPermission: true,
    requestBadgePermission: true,
    requestSoundPermission: true,
  );
  
  final InitializationSettings initializationSettings = InitializationSettings(
    android: initializationSettingsAndroid,
    iOS: initializationSettingsIOS,
  );
  
  await flutterLocalNotificationsPlugin.initialize(
    initializationSettings,
    onDidReceiveNotificationResponse: (NotificationResponse notificationResponse) {
      print('Notification clicked: ${notificationResponse.payload}');
    },
  );
}

// 显示本地通知
Future<void> showNotification(String title, String body) async {
  const AndroidNotificationDetails androidPlatformChannelSpecifics =
      AndroidNotificationDetails(
    'kitchen_safety_channel',
    'Kitchen Safety Alerts',
    channelDescription: 'Alerts for kitchen safety monitoring',
    importance: Importance.max,
    priority: Priority.high,
  );
  
  const NotificationDetails platformChannelSpecifics =
      NotificationDetails(android: androidPlatformChannelSpecifics);
  
  await flutterLocalNotificationsPlugin.show(
    0,
    title,
    body,
    platformChannelSpecifics,
    payload: 'kitchen_alert',
  );
}

class MyApp extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: '智能厨房安全系统',
      theme: ThemeData(
        primarySwatch: Colors.blue,
        visualDensity: VisualDensity.adaptivePlatformDensity,
      ),
      home: KitchenMonitorPage(),
    );
  }
}

class KitchenMonitorPage extends StatefulWidget {
  @override
  _KitchenMonitorPageState createState() => _KitchenMonitorPageState();
}

class _KitchenMonitorPageState extends State<KitchenMonitorPage> {
  // PubNub 配置
  final PubNub _pubnub = PubNub(
    defaultKeyset: Keyset(
      subscribeKey: 'sub-c-7c1de1d9-ea5b-451f-bb88-35ae502a81c4',
      publishKey: 'pub-c-85ba3694-4855-4861-a14b-fdfcb90cf839',
      uuid: UUID('flutter_app_user'),
    ),
  );
  
  final String _channel = 'chenweisong728';
  
  // 状态变量
  bool _isAlarmActive = false;
  bool _isHeatingActive = false;
  bool _isMotionDetected = false;
  bool _isFanActive = false;
  int _lastMotionSeconds = 0;
  String _lastUpdateTime = '';
  
  // 消息历史
  List<Map<String, dynamic>> _messageHistory = [];
  
  @override
  void initState() {
    super.initState();
    _initPubNub();
  }
  
  void _initPubNub() {
    // 订阅频道
    _pubnub.subscribe(channels: {_channel});
    
    // 监听消息
    _pubnub.subscribe.messages.listen((envelope) {
      final message = envelope.content as Map<String, dynamic>;
      print('Received message: $message');
      
      // 添加到历史记录
      setState(() {
        _messageHistory.insert(0, {
          'timestamp': DateTime.now().toString(),
          'message': message
        });
        
        // 限制历史记录数量
        if (_messageHistory.length > 20) {
          _messageHistory.removeLast();
        }
      });
      
      // 处理消息类型
      _processMessage(message);
    });
    
    // 发送初始状态请求
    _requestStatus();
  }
  
  void _processMessage(Map<String, dynamic> message) {
    // 检查是否是报警消息
    if (message.containsKey('alert') && message['alert'] == 'fire_hazard') {
      setState(() {
        _isAlarmActive = true;
      });
      
      // 显示报警通知
      showNotification('厨房安全警报', '检测到无人看管的加热设备，请立即查看!');
    } 
    
    // 检查是否是状态更新
    if (message.containsKey('status')) {
      switch (message['status']) {
        case 'device_status':
          setState(() {
            _isMotionDetected = message['motion_detected'] ?? false;
            _isHeatingActive = message['heating_active'] ?? false;
            _isAlarmActive = message['alarm_active'] ?? false;
            _isFanActive = message['fan_active'] ?? false;
            _lastMotionSeconds = message['last_motion'] ?? 0;
            _lastUpdateTime = DateTime.now().toString().substring(11, 19);
          });
          break;
        
        case 'alarm_reset':
          setState(() {
            _isAlarmActive = false;
          });
          break;
        
        case 'fan_status':
          setState(() {
            _isFanActive = message['fan_active'] ?? false;
          });
          break;
        
        case 'auto_safety':
          setState(() {
            _isFanActive = true;
          });
          
          // 显示自动安全措施通知
          showNotification('自动安全措施已启动', '通风扇已自动激活以防止过热');
          break;
      }
    }
    
    // 检查是否是温度传感器数据
    if (message.containsKey('sensor') && message['sensor'] == 'temperature') {
      setState(() {
        _isHeatingActive = message['heating_active'] ?? false;
      });
    }
  }
  
  void _requestStatus() {
    _pubnub.publish(
      _channel,
      {'request': 'status_update'},
    );
  }
  
  void _resetAlarm() {
    _pubnub.publish(
      _channel,
      {'reset_alarm': true},
    );
  }
  
  void _toggleFan() {
    _pubnub.publish(
      _channel,
      {'fan_control': _isFanActive ? 'off' : 'on'},
    );
  }
  
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text('智能厨房安全系统'),
        actions: [
          IconButton(
            icon: Icon(Icons.refresh),
            onPressed: _requestStatus,
            tooltip: '刷新状态',
          ),
        ],
      ),
      body: SingleChildScrollView(
        child: Column(
          children: [
            // 状态卡片
            _buildStatusCard(),
            
            // 警报和控制区域
            _buildAlarmControl(),
            
            // 消息历史
            _buildMessageHistory(),
          ],
        ),
      ),
    );
  }
  
  Widget _buildStatusCard() {
    return Card(
      margin: EdgeInsets.all(16),
      child: Padding(
        padding: EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('系统状态', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
            SizedBox(height: 16),
            
            _buildStatusRow('动作检测', _isMotionDetected ? '已检测' : '未检测',
                _isMotionDetected ? Colors.green : Colors.grey),
            
            _buildStatusRow('加热状态', _isHeatingActive ? '活跃' : '未活跃',
                _isHeatingActive ? Colors.orange : Colors.grey),
            
            _buildStatusRow('报警状态', _isAlarmActive ? '激活' : '未激活',
                _isAlarmActive ? Colors.red : Colors.grey),
            
            _buildStatusRow('通风扇', _isFanActive ? '运行中' : '停止',
                _isFanActive ? Colors.blue : Colors.grey),
            
            _buildStatusRow('最后动作', '$_lastMotionSeconds 秒前', Colors.black),
            
            _buildStatusRow('更新时间', _lastUpdateTime, Colors.black),
          ],
        ),
      ),
    );
  }
  
  Widget _buildStatusRow(String label, String value, Color color) {
    return Padding(
      padding: EdgeInsets.symmetric(vertical: 8),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(label, style: TextStyle(fontSize: 16)),
          Row(
            children: [
              Container(
                width: 12,
                height: 12,
                decoration: BoxDecoration(
                  color: color,
                  shape: BoxShape.circle,
                ),
                margin: EdgeInsets.only(right: 8),
              ),
              Text(value, style: TextStyle(fontSize: 16, fontWeight: FontWeight.w500)),
            ],
          ),
        ],
      ),
    );
  }
  
  Widget _buildAlarmControl() {
    return Card(
      margin: EdgeInsets.symmetric(horizontal: 16),
      child: Padding(
        padding: EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('控制面板', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
            SizedBox(height: 16),
            
            if (_isAlarmActive)
              Container(
                width: double.infinity,
                padding: EdgeInsets.all(16),
                decoration: BoxDecoration(
                  color: Colors.red.shade100,
                  borderRadius: BorderRadius.circular(8),
                ),
                child: Column(
                  children: [
                    Text(
                      '警报：检测到无人看管的加热设备',
                      style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold, color: Colors.red),
                    ),
                    SizedBox(height: 16),
                    ElevatedButton(
                      onPressed: _resetAlarm,
                      style: ElevatedButton.styleFrom(
                        backgroundColor: Colors.red,
                        foregroundColor: Colors.white,
                      ),
                      child: Text('解除警报'),
                    ),
                  ],
                ),
              ),
            
            SizedBox(height: 16),
            
            // 通风扇控制
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text('通风扇控制', style: TextStyle(fontSize: 16)),
                Switch(
                  value: _isFanActive,
                  onChanged: (value) => _toggleFan(),
                  activeColor: Colors.blue,
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }
  
  Widget _buildMessageHistory() {
    return Card(
      margin: EdgeInsets.all(16),
      child: Padding(
        padding: EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text('消息历史', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
                IconButton(
                  icon: Icon(Icons.delete_outline),
                  onPressed: () {
                    setState(() {
                      _messageHistory.clear();
                    });
                  },
                  tooltip: '清除历史',
                ),
              ],
            ),
            SizedBox(height: 8),
            
            // 消息列表
            _messageHistory.isEmpty
                ? Center(
                    child: Padding(
                      padding: EdgeInsets.all(16),
                      child: Text('暂无消息记录'),
                    ),
                  )
                : ListView.builder(
                    shrinkWrap: true,
                    physics: NeverScrollableScrollPhysics(),
                    itemCount: _messageHistory.length,
                    itemBuilder: (context, index) {
                      final item = _messageHistory[index];
                      return ListTile(
                        dense: true,
                        title: Text(
                          item['timestamp'].toString().substring(11, 19),
                          style: TextStyle(fontSize: 12, color: Colors.grey),
                        ),
                        subtitle: Text(
                          item['message'].toString(),
                          style: TextStyle(fontSize: 14),
                        ),
                      );
                    },
                  ),
          ],
        ),
      ),
    );
  }
  
  @override
  void dispose() {
    // 取消订阅
    _pubnub.unsubscribe(channels: {_channel});
    super.dispose();
  }
}
