import 'dart:convert';

import 'package:path/path.dart' as p;
import 'package:sqflite/sqflite.dart';

import '../models/prompt_item.dart';

class PromptDatabase {
  PromptDatabase._();
  static final PromptDatabase instance = PromptDatabase._();

  Database? _db;

  static const String tablePrompts = 'prompts';

  Future<Database> get database async {
    if (_db != null) return _db!;
    final dbPath = await getDatabasesPath();
    _db = await openDatabase(
      p.join(dbPath, 'prompt_vault.db'),
      version: 1,
      onCreate: (db, version) async {
        await db.execute('''
          CREATE TABLE $tablePrompts(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            category TEXT NOT NULL,
            tags TEXT,
            created_at TEXT NOT NULL,
            favorite INTEGER NOT NULL DEFAULT 0,
            usage_count INTEGER NOT NULL DEFAULT 0,
            last_used_at TEXT
          )
        ''');
      },
    );
    return _db!;
  }

  Future<List<PromptItem>> getAll() async {
    final db = await database;
    final rows = await db.query(tablePrompts, orderBy: 'created_at DESC');
    return rows.map(PromptItem.fromMap).toList();
  }

  Future<int> insert(PromptItem prompt) async {
    final db = await database;
    return db.insert(tablePrompts, prompt.toMap());
  }

  Future<void> update(PromptItem prompt) async {
    final db = await database;
    await db.update(
      tablePrompts,
      prompt.toMap(),
      where: 'id = ?',
      whereArgs: [prompt.id],
    );
  }

  Future<void> delete(int id) async {
    final db = await database;
    await db.delete(tablePrompts, where: 'id = ?', whereArgs: [id]);
  }

  Future<String> exportJson() async {
    final prompts = await getAll();
    final data = prompts.map((p) => p.toMap()).toList();
    return const JsonEncoder.withIndent('  ').convert(data);
  }

  Future<void> importJson(String jsonString) async {
    final db = await database;
    final List<dynamic> raw = jsonDecode(jsonString) as List<dynamic>;

    await db.transaction((txn) async {
      for (final item in raw) {
        final map = Map<String, Object?>.from(item as Map);
        map.remove('id');
        await txn.insert(tablePrompts, map);
      }
    });
  }
}
