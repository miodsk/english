# NestJS 使用 Socket.io 完整指南

本文档详细介绍如何在 NestJS 中集成和使用 Socket.io，包括后端和前端的完整实现。

## 快速参考

### 后端装饰器

#### @WebSocketGateway(options)

标记类为 WebSocket 网关，配置命名空间、CORS 等。

```typescript
@WebSocketGateway({
  namespace: 'chat',
  cors: { origin: '*', credentials: true },
})
export class ChatGateway {}
```

#### @SubscribeMessage(event)

订阅客户端发送的特定事件。

```typescript
@SubscribeMessage('message')
handleMessage(@MessageBody() data: string) {
  return { received: data };
}
```

#### @WebSocketServer()

注入 Socket.io Server 实例，用于广播消息。

```typescript
export class ChatGateway {
  @WebSocketServer()
  server: Server;

  broadcast() {
    this.server.emit('notification', 'Hello all!');
  }
}
```

#### @ConnectedSocket()

注入当前连接的 Socket 实例。

```typescript
@SubscribeMessage('ping')
handlePing(@ConnectedSocket() client: Socket) {
  console.log('Client ID:', client.id);
  client.emit('pong', 'Pong!');
}
```

#### @MessageBody()

获取消息数据，支持管道验证。

```typescript
@SubscribeMessage('message')
handleMessage(@MessageBody() data: { text: string }) {
  console.log('Message:', data.text);
}

// 带验证
@SubscribeMessage('message')
handleMessage(@MessageBody(new ValidationPipe()) data: MessageDto) {}
```

#### @UseGuards()

应用守卫进行权限控制。

```typescript
@WebSocketGateway()
@UseGuards(WsJwtGuard)
export class ChatGateway {}
```

#### @UseInterceptors()

应用拦截器进行数据处理。

```typescript
@WebSocketGateway()
@UseInterceptors(WsLoggingInterceptor)
export class ChatGateway {}
```

#### @UsePipes()

应用管道进行数据验证。

```typescript
@SubscribeMessage('message')
handleMessage(
  @MessageBody(new ValidationPipe()) data: MessageDto,
) {}
```

#### @UseFilters()

应用异常过滤器。

```typescript
@WebSocketGateway()
@UseFilters(new WsExceptionFilter())
export class ChatGateway {}
```

---

### 后端生命周期钩子

#### OnGatewayConnection

客户端连接时触发，用于身份验证和初始化。

```typescript
export class ChatGateway implements OnGatewayConnection {
  handleConnection(client: Socket) {
    console.log('Client connected:', client.id);
    // 身份验证
    const token = client.handshake.auth.token;
    if (!token) client.disconnect(true);
  }
}
```

#### OnGatewayDisconnect

客户端断开时触发，用于清理资源。

```typescript
export class ChatGateway implements OnGatewayDisconnect {
  handleDisconnect(client: Socket) {
    console.log('Client disconnected:', client.id);
    // 清理用户数据
    this.userService.removeOnlineUser(client.id);
  }
}
```

#### OnGatewayInit

网关初始化完成后触发，可访问服务器实例。

```typescript
export class ChatGateway implements OnGatewayInit {
  afterInit(server: Server) {
    console.log('Gateway initialized');
    server.emit('serverReady', { timestamp: Date.now() });
  }
}
```

---

### 前端 API

#### io(url, options)

创建 Socket 连接。

```typescript
const socket = io('http://localhost:3000/chat', {
  auth: { token: 'jwt-token' },
  transports: ['websocket'],
});
```

#### socket.emit(event, data)

发送事件到服务器。

```typescript
socket.emit('message', { room: 'general', text: 'Hello!' });
```

#### socket.on(event, callback)

监听服务器事件。

```typescript
socket.on('message', (data) => {
  console.log('Received:', data);
});
```

#### socket.on('connect')

连接成功事件。

```typescript
socket.on('connect', () => {
  console.log('Connected! ID:', socket.id);
});
```

#### socket.on('disconnect')

断开连接事件。

```typescript
socket.on('disconnect', (reason) => {
  console.log('Disconnected:', reason);
});
```

#### socket.on('connect_error')

连接错误事件。

```typescript
socket.on('connect_error', (error) => {
  console.error('Connection failed:', error);
});
```

#### socket.disconnect()

主动断开连接。

```typescript
socket.disconnect();
```

---

### Server 方法（后端）

#### server.emit(event, data)

向所有客户端广播。

```typescript
this.server.emit('notification', { message: 'System update!' });
```

#### server.to(room).emit()

向指定房间广播。

```typescript
this.server.to('general').emit('message', { text: 'Hello room!' });
```

#### server.in(room).emit()

同 to()，向房间广播。

```typescript
this.server.in('general').emit('message', 'Hello!');
```

#### server.of(namespace)

获取命名空间实例。

```typescript
const chatNamespace = this.server.of('/chat');
chatNamespace.emit('system', 'Welcome!');
```

#### server.socketsJoin(room)

所有客户端加入房间。

```typescript
this.server.socketsJoin('announcement');
```

#### server.socketsLeave(room)

所有客户端离开房间。

```typescript
this.server.socketsLeave('announcement');
```

#### server.fetchSockets()

获取所有活跃连接。

```typescript
const sockets = await this.server.fetchSockets();
console.log('Active connections:', sockets.length);

## 目录

- [简介](#简介)
- [后端实现](#后端实现)
- [前端实现](#前端实现)
- [高级用法](#高级用法)
- [最佳实践](#最佳实践)
## 简介

Socket.io 是一个基于 WebSocket 的实时通信库，提供双向、低延迟的通信能力。NestJS 通过 `@nestjs/platform-socket.io` 提供了对 Socket.io 的原生支持。

### 核心概念

- **Gateway（网关）**：NestJS 中处理 WebSocket 连接的类，相当于控制器
- **Socket**：客户端与服务器之间的连接实例
- **Namespace**：用于分隔不同功能的通信通道
- **Room**：用于在命名空间内对客户端进行分组

## 后端实现

### 1. 安装依赖

```bash
npm install @nestjs/websockets @nestjs/platform-socket.io socket.io
# 或使用 pnpm
pnpm add @nestjs/websockets @nestjs/platform-socket.io socket.io
```

### 2. 创建 Gateway

```typescript
// src/chat/chat.gateway.ts
import {
  WebSocketGateway,
  SubscribeMessage,
  WsResponse,
  WebSocketServer,
  ConnectedSocket,
  MessageBody,
  OnGatewayConnection,
  OnGatewayDisconnect,
} from '@nestjs/websockets';
import { Server, Socket } from 'socket.io';
import { Logger } from '@nestjs/common';

@WebSocketGateway({
  namespace: 'chat',
  cors: {
    origin: '*', // 生产环境应配置具体的源
    credentials: true,
  },
})
export class ChatGateway implements OnGatewayConnection, OnGatewayDisconnect {
  @WebSocketServer()
  server: Server;

  private logger: Logger = new Logger('ChatGateway');

  handleConnection(client: Socket) {
    this.logger.log(`Client connected: ${client.id}`);
    // 可以在这里进行身份验证
    // const token = client.handshake.auth.token;
  }

  handleDisconnect(client: Socket) {
    this.logger.log(`Client disconnected: ${client.id}`);
  }

  @SubscribeMessage('message')
  handleMessage(
    @ConnectedSocket() client: Socket,
    @MessageBody() data: { room: string; message: string },
  ): void {
    // 广播消息到指定房间
    this.server.to(data.room).emit('message', {
      user: client.id,
      message: data.message,
      timestamp: new Date(),
    });
  }

  @SubscribeMessage('joinRoom')
  handleJoinRoom(
    @ConnectedSocket() client: Socket,
    @MessageBody() room: string,
  ): void {
    client.join(room);
    this.logger.log(`Client ${client.id} joined room: ${room}`);
    
    // 通知房间内其他人
    client.to(room).emit('userJoined', {
      user: client.id,
      room: room,
    });
  }

  @SubscribeMessage('leaveRoom')
  handleLeaveRoom(
    @ConnectedSocket() client: Socket,
    @MessageBody() room: string,
  ): void {
    client.leave(room);
    this.logger.log(`Client ${client.id} left room: ${room}`);
    
    // 通知房间内其他人
    client.to(room).emit('userLeft', {
      user: client.id,
      room: room,
    });
  }
}
```

### 3. 注册模块

```typescript
// src/chat/chat.module.ts
import { Module } from '@nestjs/common';
import { ChatGateway } from './chat.gateway';

@Module({
  providers: [ChatGateway],
})
export class ChatModule {}
```

```typescript
// src/app.module.ts
import { Module } from '@nestjs/common';
import { ChatModule } from './chat/chat.module';

@Module({
  imports: [ChatModule],
})
export class AppModule {}
```

### 4. 带身份验证的 Gateway

```typescript
// src/chat/chat.gateway.ts
import {
  WebSocketGateway,
  SubscribeMessage,
  WebSocketServer,
  ConnectedSocket,
  MessageBody,
  OnGatewayConnection,
} from '@nestjs/websockets';
import { Server, Socket } from 'socket.io';
import { Logger, UnauthorizedException } from '@nestjs/common';
import { JwtService } from '@nestjs/jwt';

@WebSocketGateway({
  namespace: 'chat',
  cors: {
    origin: '*',
    credentials: true,
  },
})
export class ChatGateway implements OnGatewayConnection {
  @WebSocketServer()
  server: Server;

  private logger: Logger = new Logger('ChatGateway');

  constructor(private jwtService: JwtService) {}

  async handleConnection(client: Socket) {
    try {
      const token = client.handshake.auth.token || 
                    client.handshake.headers.authorization?.split(' ')[1];
      
      if (!token) {
        throw new UnauthorizedException('Token not provided');
      }

      const payload = await this.jwtService.verifyAsync(token);
      // 将用户信息附加到 socket 实例
      client.data.user = payload;
      this.logger.log(`Client authenticated: ${client.id}, User: ${payload.sub}`);
    } catch (error) {
      this.logger.error(`Authentication failed: ${error.message}`);
      client.disconnect(true);
    }
  }

  @SubscribeMessage('message')
  handleMessage(
    @ConnectedSocket() client: Socket,
    @MessageBody() data: { room: string; message: string },
  ): void {
    const user = client.data.user;
    
    this.server.to(data.room).emit('message', {
      userId: user.sub,
      username: user.username,
      message: data.message,
      timestamp: new Date(),
    });
  }
}
```

### 5. WebSocket 适配器（可选）

如果需要自定义配置或使用其他 WebSocket 库，可以创建适配器：

```typescript
// src/websocket-adapter.ts
import { IoAdapter } from '@nestjs/platform-socket.io';
import { ServerOptions } from 'socket.io';
import { INestApplicationContext } from '@nestjs/common';

export class CustomIoAdapter extends IoAdapter {
  constructor(private app: INestApplicationContext) {
    super(app);
  }

  createIOServer(port: number, options?: ServerOptions) {
    const server = super.createIOServer(port, {
      ...options,
      cors: {
        origin: ['http://localhost:3000', 'https://yourdomain.com'],
        credentials: true,
      },
      // 其他自定义配置
      pingTimeout: 60000,
      pingInterval: 25000,
    });
    return server;
  }
}
```

在 `main.ts` 中使用：

```typescript
// src/main.ts
import { NestFactory } from '@nestjs/core';
import { AppModule } from './app.module';
import { CustomIoAdapter } from './websocket-adapter';

async function bootstrap() {
  const app = await NestFactory.create(AppModule);
  
  // 使用自定义适配器
  app.useWebSocketAdapter(new CustomIoAdapter(app));
  
  await app.listen(3000);
}
bootstrap();
```

## 前端实现

### 1. 安装依赖

```bash
npm install socket.io-client
# 或
pnpm add socket.io-client
```

### 2. React 示例

#### 基础 Hook 封装

```typescript
// src/hooks/useSocket.ts
import { useEffect, useState, useRef } from 'react';
import { io, Socket } from 'socket.io-client';

interface UseSocketOptions {
  url: string;
  namespace?: string;
  auth?: {
    token?: string;
  };
}

export function useSocket({ url, namespace = '', auth }: UseSocketOptions) {
  const [socket, setSocket] = useState<Socket | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const socketRef = useRef<Socket>();

  useEffect(() => {
    const socketUrl = namespace ? `${url}/${namespace}` : url;
    
    const newSocket = io(socketUrl, {
      auth: auth,
      transports: ['websocket'],
      reconnection: true,
      reconnectionAttempts: 5,
      reconnectionDelay: 1000,
    });

    socketRef.current = newSocket;
    setSocket(newSocket);

    newSocket.on('connect', () => {
      setIsConnected(true);
      console.log('Socket connected:', newSocket.id);
    });

    newSocket.on('disconnect', (reason) => {
      setIsConnected(false);
      console.log('Socket disconnected:', reason);
    });

    newSocket.on('connect_error', (error) => {
      console.error('Connection error:', error);
    });

    return () => {
      newSocket.disconnect();
    };
  }, [url, namespace, auth?.token]);

  return { socket, isConnected };
}
```

#### 聊天组件示例

```typescript
// src/components/Chat.tsx
import React, { useState, useEffect, useRef } from 'react';
import { io, Socket } from 'socket.io-client';

interface Message {
  userId: string;
  username: string;
  message: string;
  timestamp: Date;
}

export function Chat({ token }: { token: string }) {
  const [socket, setSocket] = useState<Socket | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [message, setMessage] = useState('');
  const [room, setRoom] = useState('general');
  const [isConnected, setIsConnected] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const newSocket = io('http://localhost:3000/chat', {
      auth: { token },
      transports: ['websocket'],
    });

    setSocket(newSocket);

    newSocket.on('connect', () => {
      setIsConnected(true);
      newSocket.emit('joinRoom', room);
    });

    newSocket.on('disconnect', () => {
      setIsConnected(false);
    });

    newSocket.on('message', (data: Message) => {
      setMessages((prev) => [...prev, data]);
    });

    newSocket.on('userJoined', (data) => {
      setMessages((prev) => [
        ...prev,
        {
          userId: 'system',
          username: 'System',
          message: `User ${data.user} joined the room`,
          timestamp: new Date(),
        },
      ]);
    });

    return () => {
      newSocket.disconnect();
    };
  }, [token]);

  useEffect(() => {
    if (socket && room) {
      socket.emit('joinRoom', room);
    }
  }, [room, socket]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const sendMessage = () => {
    if (socket && message.trim()) {
      socket.emit('message', {
        room,
        message: message.trim(),
      });
      setMessage('');
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  return (
    <div className="chat-container">
      <div className="chat-header">
        <span className={`status ${isConnected ? 'connected' : 'disconnected'}`}>
          {isConnected ? '🟢 Connected' : '🔴 Disconnected'}
        </span>
        <select value={room} onChange={(e) => setRoom(e.target.value)}>
          <option value="general">General</option>
          <option value="random">Random</option>
          <option value="support">Support</option>
        </select>
      </div>

      <div className="messages">
        {messages.map((msg, index) => (
          <div key={index} className="message">
            <span className="username">{msg.username}:</span>
            <span className="text">{msg.message}</span>
            <span className="time">
              {new Date(msg.timestamp).toLocaleTimeString()}
            </span>
          </div>
        ))}
        <div ref={messagesEndRef} />
      </div>

      <div className="input-container">
        <input
          type="text"
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          onKeyPress={handleKeyPress}
          placeholder="Type a message..."
          disabled={!isConnected}
        />
        <button onClick={sendMessage} disabled={!isConnected}>
          Send
        </button>
      </div>

      <style>{`
        .chat-container {
          max-width: 800px;
          margin: 0 auto;
          border: 1px solid #ddd;
          border-radius: 8px;
          overflow: hidden;
        }
        .chat-header {
          display: flex;
          justify-content: space-between;
          padding: 15px;
          background: #f5f5f5;
          border-bottom: 1px solid #ddd;
        }
        .messages {
          height: 400px;
          overflow-y: auto;
          padding: 15px;
        }
        .message {
          margin-bottom: 10px;
          padding: 8px;
          border-radius: 4px;
          background: #f9f9f9;
        }
        .username {
          font-weight: bold;
          margin-right: 8px;
        }
        .time {
          float: right;
          font-size: 0.8em;
          color: #666;
        }
        .input-container {
          display: flex;
          padding: 15px;
          border-top: 1px solid #ddd;
        }
        input {
          flex: 1;
          padding: 10px;
          border: 1px solid #ddd;
          border-radius: 4px;
          margin-right: 10px;
        }
        button {
          padding: 10px 20px;
          background: #007bff;
          color: white;
          border: none;
          border-radius: 4px;
          cursor: pointer;
        }
        button:disabled {
          background: #ccc;
          cursor: not-allowed;
        }
        .connected {
          color: green;
        }
        .disconnected {
          color: red;
        }
      `}</style>
    </div>
  );
}
```

## 高级用法
## 高级用法

### 1. 命名空间隔离

使用命名空间分隔不同的功能模块：

```typescript
// 聊天命名空间
@WebSocketGateway({ namespace: 'chat' })
export class ChatGateway {}

// 通知命名空间
@WebSocketGateway({ namespace: 'notifications' })
export class NotificationGateway {}

// 游戏命名空间
@WebSocketGateway({ namespace: 'game' })
export class GameGateway {}
```

前端连接：

```typescript
const chatSocket = io('http://localhost:3000/chat');
const notificationSocket = io('http://localhost:3000/notifications');
const gameSocket = io('http://localhost:3000/game');
```

### 2. 使用拦截器进行数据处理

```typescript
// src/common/interceptors/ws-logging.interceptor.ts
import {
  Injectable,
  NestInterceptor,
  ExecutionContext,
  CallHandler,
} from '@nestjs/common';
import { Observable } from 'rxjs';
import { tap } from 'rxjs/operators';
import { Socket } from 'socket.io';

@Injectable()
export class WsLoggingInterceptor implements NestInterceptor {
  intercept(context: ExecutionContext, next: CallHandler): Observable<any> {
    const client: Socket = context.switchToWs().getClient();
    const event = context.switchToWs().getPattern();
    
    console.log(`Before: ${event} from ${client.id}`);
    
    const now = Date.now();
    return next
      .handle()
      .pipe(
        tap(() => console.log(`After: ${event} - ${Date.now() - now}ms`)),
      );
  }
}
```

在 Gateway 中使用：

```typescript
@WebSocketGateway({ namespace: 'chat' })
@UseInterceptors(WsLoggingInterceptor)
export class ChatGateway {
  // ...
}
```

### 3. 使用守卫进行权限控制

```typescript
// src/common/guards/ws-jwt.guard.ts
import {
  CanActivate,
  ExecutionContext,
  Injectable,
  UnauthorizedException,
} from '@nestjs/common';
import { JwtService } from '@nestjs/jwt';
import { Socket } from 'socket.io';

@Injectable()
export class WsJwtGuard implements CanActivate {
  constructor(private jwtService: JwtService) {}

  async canActivate(context: ExecutionContext): Promise<boolean> {
    const client: Socket = context.switchToWs().getClient();
    
    const token = client.handshake.auth.token || 
                  client.handshake.headers.authorization?.split(' ')[1];
    
    if (!token) {
      throw new UnauthorizedException('Token not provided');
    }

    try {
      const payload = await this.jwtService.verifyAsync(token);
      client.data.user = payload;
      return true;
    } catch (error) {
      throw new UnauthorizedException('Invalid token');
    }
  }
}
```

在 Gateway 中使用：

```typescript
@WebSocketGateway({ namespace: 'chat' })
@UseGuards(WsJwtGuard)
export class ChatGateway {
  @SubscribeMessage('message')
  handleMessage(
    @ConnectedSocket() client: Socket,
    @MessageBody() data: any,
  ): void {
    const user = client.data.user;
    // 只有通过认证的用户才能发送消息
  }
}
```

### 4. 使用过滤器处理错误

```typescript
// src/common/filters/ws-exception.filter.ts
import {
  ArgumentsHost,
  Catch,
  ExceptionFilter,
  BadRequestException,
  UnauthorizedException,
} from '@nestjs/common';
import { Socket } from 'socket.io';

@Catch()
export class WsExceptionFilter implements ExceptionFilter {
  catch(exception: any, host: ArgumentsHost) {
    const client: Socket = host.switchToWs().getClient();
    
    let message = 'Internal server error';
    let event = 'error';
    
    if (exception instanceof BadRequestException) {
      message = 'Bad request';
    } else if (exception instanceof UnauthorizedException) {
      message = 'Unauthorized';
      event = 'unauthorized';
    }
    
    client.emit(event, {
      success: false,
      message,
      timestamp: new Date(),
    });
  }
}
```

在 Gateway 中使用：

```typescript
@WebSocketGateway({ namespace: 'chat' })
@UseFilters(new WsExceptionFilter())
export class ChatGateway {
  // ...
}
```

### 5. 使用 Pipe 进行数据验证

```typescript
// src/chat/dto/message.dto.ts
import { IsString, IsNotEmpty, MaxLength } from 'class-validator';

export class MessageDto {
  @IsString()
  @IsNotEmpty()
  @MaxLength(500)
  room: string;

  @IsString()
  @IsNotEmpty()
  @MaxLength(1000)
  message: string;
}
```

```typescript
// src/common/pipes/ws-validation.pipe.ts
import { PipeTransform, Injectable, ArgumentMetadata, BadRequestException } from '@nestjs/common';
import { validate } from 'class-validator';
import { plainToInstance } from 'class-transformer';

@Injectable()
export class WsValidationPipe implements PipeTransform {
  async transform(value: any, { metatype }: ArgumentMetadata) {
    if (!metatype || !this.toValidate(metatype)) {
      return value;
    }
    
    const object = plainToInstance(metatype, value);
    const errors = await validate(object);
    
    if (errors.length > 0) {
      const messages = errors.map(error => 
        Object.values(error.constraints).join(', ')
      ).join('; ');
      
      throw new BadRequestException(messages);
    }
    
    return value;
  }

  private toValidate(metatype: Function): boolean {
    const types: Function[] = [String, Boolean, Number, Array, Object];
    return !types.includes(metatype);
  }
}
```

在 Gateway 中使用：

```typescript
@SubscribeMessage('message')
handleMessage(
  @ConnectedSocket() client: Socket,
  @MessageBody(new WsValidationPipe()) data: MessageDto,
): void {
  // data 已经通过验证
}
```

### 6. Redis 适配器（用于多实例部署）

当应用有多个实例时，使用 Redis 适配器同步 Socket.io 消息：

```bash
pnpm add @socket.io/redis-adapter redis
```

```typescript
// src/main.ts
import { NestFactory } from '@nestjs/core';
import { AppModule } from './app.module';
import { IoAdapter } from '@nestjs/platform-socket.io';
import { createAdapter } from '@socket.io/redis-adapter';
import { createClient } from 'redis';

async function bootstrap() {
  const app = await NestFactory.create(AppModule);

  const pubClient = createClient({
    host: 'localhost',
    port: 6379,
  });
  const subClient = pubClient.duplicate();

  await Promise.all([pubClient.connect(), subClient.connect()]);

  const redisIoAdapter = new IoAdapter(app);
  redisIoAdapter.createIOServer = (port, options) => {
    const server = require('socket.io')(port, options);
    server.adapter(createAdapter(pubClient, subClient));
    return server;
  };

  app.useWebSocketAdapter(redisIoAdapter);

  await app.listen(3000);
}
bootstrap();
```

## 最佳实践

### 1. 连接管理

- 在 `handleConnection` 中进行身份验证
- 在 `handleDisconnect` 中清理资源
- 设置合理的超时和重连策略

```typescript
// 前端
const socket = io(url, {
  reconnection: true,
  reconnectionAttempts: 5,
  reconnectionDelay: 1000,
  reconnectionDelayMax: 5000,
  timeout: 20000,
});
```

### 2. 错误处理

- 使用统一的错误格式
- 记录所有错误日志
- 为客户端提供清晰的错误信息

```typescript
socket.on('error', (error) => {
  console.error('Socket error:', error);
  // 显示用户友好的错误消息
});
```

### 3. 性能优化

- 使用 WebSocket 传输方式
- 限制消息大小
- 使用房间进行消息过滤
- 避免频繁的房间切换

```typescript
// 前端
const socket = io(url, {
  transports: ['websocket'], // 直接使用 WebSocket
  upgrade: false, // 禁用升级
});
```

### 4. 安全性

- 验证所有传入的消息
- 使用 JWT 进行身份验证
- 限制命名空间和房间的访问权限
- 配置正确的 CORS

```typescript
@WebSocketGateway({
  cors: {
    origin: ['https://yourdomain.com'],
    credentials: true,
  },
})
```

### 5. 类型安全

使用 TypeScript 类型定义确保类型安全：

```typescript
// 共享类型定义
interface ServerToClientEvents {
  message: (data: Message) => void;
  userJoined: (data: { user: string; room: string }) => void;
  error: (error: { message: string }) => void;
}

interface ClientToServerEvents {
  message: (data: { room: string; message: string }) => void;
  joinRoom: (room: string) => void;
  leaveRoom: (room: string) => void;
}

// 后端
@WebSocketGateway<ServerToClientEvents, ClientToServerEvents>({
  namespace: 'chat',
})
export class ChatGateway {
  @SubscribeMessage('message')
  handleMessage(
    @ConnectedSocket() client: Socket,
    @MessageBody() data: { room: string; message: string },
  ): void {
    this.server.emit('message', {
      userId: '123',
      username: 'User',
      message: data.message,
      timestamp: new Date(),
    });
  }
}

// 前端
import { io, Socket } from 'socket.io-client';

const socket: Socket<ServerToClientEvents, ClientToServerEvents> = 
  io('http://localhost:3000/chat');

socket.emit('message', { room: 'general', message: 'Hello' });

socket.on('message', (data) => {
  console.log(data.message); // 类型安全
});
```

### 6. 测试

#### 单元测试

```typescript
// src/chat/chat.gateway.spec.ts
import { Test, TestingModule } from '@nestjs/testing';
import { ChatGateway } from './chat.gateway';
import { Socket } from 'socket.io';

describe('ChatGateway', () => {
  let gateway: ChatGateway;

  beforeEach(async () => {
    const module: TestingModule = await Test.createTestingModule({
      providers: [ChatGateway],
    }).compile();

    gateway = module.get<ChatGateway>(ChatGateway);
  });

  it('should handle connection', () => {
    const client = {
      id: 'test-client-id',
      handshake: { auth: {} },
    } as Socket;

    gateway.handleConnection(client);
    // 验证连接逻辑
  });

  it('should handle message', () => {
    const client = {
      id: 'test-client-id',
    } as Socket;

    const data = { room: 'general', message: 'Hello' };

    gateway.handleMessage(client, data);
    // 验证消息处理逻辑
  });
});
```

#### E2E 测试

```typescript
// test/chat.e2e-spec.ts
import { Test, TestingModule } from '@nestjs/testing';
import { INestApplication } from '@nestjs/common';
import { AppModule } from './../src/app.module';
import { io, Socket } from 'socket.io-client';

describe('ChatGateway (e2e)', () => {
  let app: INestApplication;
  let socket: Socket;

  beforeEach(async () => {
    const moduleFixture: TestingModule = await Test.createTestingModule({
      imports: [AppModule],
    }).compile();

    app = moduleFixture.createNestApplication();
    await app.listen(3000);
  });

  afterEach(async () => {
    socket.disconnect();
    await app.close();
  });

  it('should connect and join room', (done) => {
    socket = io('http://localhost:3000/chat');

    socket.on('connect', () => {
      socket.emit('joinRoom', 'general');
      
      socket.on('userJoined', (data) => {
        expect(data.room).toBe('general');
        done();
      });
    });
  });

  it('should send and receive messages', (done) => {
    socket = io('http://localhost:3000/chat');

    socket.on('connect', () => {
      socket.emit('joinRoom', 'general');
      
      setTimeout(() => {
        socket.emit('message', {
          room: 'general',
          message: 'Test message',
        });
      }, 100);
    });

    socket.on('message', (data) => {
      expect(data.message).toBe('Test message');
      done();
    });
  });
});
```

## 总结

本文档涵盖了：

1. **后端实现**：Gateway 创建、身份验证、拦截器、守卫、过滤器
2. **前端实现**：React 的完整示例
3. **高级用法**：命名空间、Redis 适配器、类型安全
4. **最佳实践**：连接管理、错误处理、性能优化、安全性、测试

根据你的具体需求选择合适的实现方式，并遵循最佳实践以确保应用的稳定性和可维护性。

## 参考资源

- [NestJS WebSockets 官方文档](https://docs.nestjs.com/websockets/gateways)
- [Socket.io 官方文档](https://socket.io/docs/v4/)
- [Socket.io Redis 适配器](https://socket.io/docs/v4/redis-adapter/)
- [NestJS WebSocket 示例](https://github.com/nestjs/nest/tree/master/sample/16-gateways)