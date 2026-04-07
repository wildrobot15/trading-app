class PromptItem {
  PromptItem({
    this.id,
    required this.title,
    required this.content,
    required this.category,
    required this.tags,
    required this.createdAt,
    this.favorite = false,
    this.usageCount = 0,
    this.lastUsedAt,
  });

  final int? id;
  final String title;
  final String content;
  final String category;
  final List<String> tags;
  final DateTime createdAt;
  final bool favorite;
  final int usageCount;
  final DateTime? lastUsedAt;

  PromptItem copyWith({
    int? id,
    String? title,
    String? content,
    String? category,
    List<String>? tags,
    DateTime? createdAt,
    bool? favorite,
    int? usageCount,
    DateTime? lastUsedAt,
  }) {
    return PromptItem(
      id: id ?? this.id,
      title: title ?? this.title,
      content: content ?? this.content,
      category: category ?? this.category,
      tags: tags ?? this.tags,
      createdAt: createdAt ?? this.createdAt,
      favorite: favorite ?? this.favorite,
      usageCount: usageCount ?? this.usageCount,
      lastUsedAt: lastUsedAt ?? this.lastUsedAt,
    );
  }

  Map<String, Object?> toMap() {
    return {
      'id': id,
      'title': title,
      'content': content,
      'category': category,
      'tags': tags.join(','),
      'created_at': createdAt.toIso8601String(),
      'favorite': favorite ? 1 : 0,
      'usage_count': usageCount,
      'last_used_at': lastUsedAt?.toIso8601String(),
    };
  }

  factory PromptItem.fromMap(Map<String, Object?> map) {
    return PromptItem(
      id: map['id'] as int?,
      title: map['title'] as String,
      content: map['content'] as String,
      category: map['category'] as String,
      tags: (map['tags'] as String? ?? '')
          .split(',')
          .where((tag) => tag.trim().isNotEmpty)
          .toList(),
      createdAt: DateTime.parse(map['created_at'] as String),
      favorite: (map['favorite'] as int? ?? 0) == 1,
      usageCount: map['usage_count'] as int? ?? 0,
      lastUsedAt: map['last_used_at'] != null
          ? DateTime.tryParse(map['last_used_at'] as String)
          : null,
    );
  }
}
