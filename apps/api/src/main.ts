import { NestFactory } from '@nestjs/core';
import { ConfigService } from '@nestjs/config';
import { AppModule } from './app.module.js';

async function bootstrap() {
  const app = await NestFactory.create(AppModule);

  const configService = app.get(ConfigService);

  console.log('Database URL:', configService.get<string>('DATABASE_URL'));

  await app.listen(3001);

  console.log('🚀 API running at http://localhost:3001');
}

bootstrap();