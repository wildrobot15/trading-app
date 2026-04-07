import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:share_plus/share_plus.dart';

import '../models/prompt_item.dart';
import '../services/prompt_database.dart';

class PromptProvider extends ChangeNotifier {
  PromptProvider() {
    loadPrompts();
  }

  static const List<String> defaultCategories = [
    'Productivity',
    'Work / Office',
    'Cybersecurity',
    'Learning',
    'Content Creation',
    'Business Ideas',
    'Personal Use',
  ];

  final PromptDatabase _database = PromptDatabase.instance;
  final List<PromptItem> _prompts = [];

  String _query = '';
  String _categoryFilter = 'All';
  bool _favoriteOnly = false;

  List<PromptItem> get prompts => List.unmodifiable(_prompts);

  List<PromptItem> get filteredPrompts {
    return _prompts.where((prompt) {
      final byQuery = _query.isEmpty ||
          prompt.title.toLowerCase().contains(_query.toLowerCase()) ||
          prompt.content.toLowerCase().contains(_query.toLowerCase()) ||
          prompt.tags.any((tag) => tag.toLowerCase().contains(_query.toLowerCase()));
      final byCategory = _categoryFilter == 'All' || prompt.category == _categoryFilter;
      final byFavorite = !_favoriteOnly || prompt.favorite;
      return byQuery && byCategory && byFavorite;
    }).toList();
  }

  List<PromptItem> get recentPrompts {
    final sorted = [..._prompts]
      ..sort((a, b) {
        final aDate = a.lastUsedAt ?? a.createdAt;
        final bDate = b.lastUsedAt ?? b.createdAt;
        return bDate.compareTo(aDate);
      });
    return sorted.take(5).toList();
  }

  List<PromptItem> get mostUsedPrompts {
    final sorted = [..._prompts]..sort((a, b) => b.usageCount.compareTo(a.usageCount));
    return sorted.where((prompt) => prompt.usageCount > 0).take(5).toList();
  }

  Future<void> loadPrompts() async {
    _prompts
      ..clear()
      ..addAll(await _database.getAll());
    notifyListeners();
  }

  Future<void> addPrompt(PromptItem prompt) async {
    await _database.insert(prompt);
    await loadPrompts();
  }

  Future<void> updatePrompt(PromptItem prompt) async {
    await _database.update(prompt);
    await loadPrompts();
  }

  Future<void> deletePrompt(int id) async {
    await _database.delete(id);
    await loadPrompts();
  }

  Future<void> toggleFavorite(PromptItem prompt) async {
    await updatePrompt(prompt.copyWith(favorite: !prompt.favorite));
  }

  Future<void> markUsed(PromptItem prompt) async {
    await updatePrompt(
      prompt.copyWith(
        usageCount: prompt.usageCount + 1,
        lastUsedAt: DateTime.now(),
      ),
    );
  }

  void setQuery(String query) {
    _query = query.trim();
    notifyListeners();
  }

  void setCategoryFilter(String category) {
    _categoryFilter = category;
    notifyListeners();
  }

  void setFavoriteOnly(bool value) {
    _favoriteOnly = value;
    notifyListeners();
  }

  Future<void> copyPrompt(PromptItem prompt) async {
    await Clipboard.setData(ClipboardData(text: prompt.content));
    await markUsed(prompt);
  }

  Future<void> sharePrompt(PromptItem prompt) async {
    await Share.share('${prompt.title}\n\n${prompt.content}');
    await markUsed(prompt);
  }

  Future<String> exportPrompts() => _database.exportJson();
  Future<void> importPrompts(String json) async {
    await _database.importJson(json);
    await loadPrompts();
  }
}
