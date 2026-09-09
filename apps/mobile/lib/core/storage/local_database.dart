import 'dart:convert';
import 'package:sqflite/sqflite.dart';
import 'package:path/path.dart';

class LocalDatabase {
  static Database? _database;

  Future<Database> get database async {
    if (_database != null) return _database!;
    _database = await _initDB('dentalcare_offline.db');
    return _database!;
  }

  Future<Database> _initDB(String filePath) async {
    final dbPath = await getDatabasesPath();
    final path = join(dbPath, filePath);

    return await openDatabase(
      path,
      version: 1,
      onCreate: (db, version) async {
        // Cached entities table
        await db.execute('''
          CREATE TABLE cached_entities (
            id TEXT PRIMARY KEY,
            entity_type TEXT NOT NULL,
            payload_json TEXT NOT NULL,
            updated_at TEXT NOT NULL
          )
        ''');

        // Mutation queue table
        await db.execute('''
          CREATE TABLE mutation_queue (
            mutation_id TEXT PRIMARY KEY,
            entity_type TEXT NOT NULL,
            action TEXT NOT NULL,
            entity_id TEXT,
            payload_json TEXT NOT NULL,
            created_at TEXT NOT NULL,
            retry_count INTEGER DEFAULT 0
          )
        ''');
      },
    );
  }

  Future<void> cacheEntity(String id, String type, Map<String, dynamic> data) async {
    final db = await database;
    await db.insert(
      'cached_entities',
      {
        'id': id,
        'entity_type': type,
        'payload_json': jsonEncode(data),
        'updated_at': DateTime.now().toIso8601String(),
      },
      conflictAlgorithm: ConflictAlgorithm.replace,
    );
  }

  Future<List<Map<String, dynamic>>> getCachedEntities(String type) async {
    final db = await database;
    final results = await db.query(
      'cached_entities',
      where: 'entity_type = ?',
      whereArgs: [type],
    );
    return results.map((r) => jsonDecode(r['payload_json'] as String) as Map<String, dynamic>).toList();
  }

  Future<void> enqueueMutation({
    required String mutationId,
    required String entityType,
    required String action,
    String? entityId,
    required Map<String, dynamic> payload,
  }) async {
    final db = await database;
    await db.insert(
      'mutation_queue',
      {
        'mutation_id': mutationId,
        'entity_type': entityType,
        'action': action,
        'entity_id': entityId,
        'payload_json': jsonEncode(payload),
        'created_at': DateTime.now().toIso8601String(),
        'retry_count': 0,
      },
      conflictAlgorithm: ConflictAlgorithm.replace,
    );
  }

  Future<List<Map<String, dynamic>>> getPendingMutations() async {
    final db = await database;
    return await db.query('mutation_queue', orderBy: 'created_at ASC');
  }

  Future<void> removeMutation(String mutationId) async {
    final db = await database;
    await db.delete('mutation_queue', where: 'mutation_id = ?', whereArgs: [mutationId]);
  }
}
