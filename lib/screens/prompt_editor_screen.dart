import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../models/prompt_item.dart';
import '../providers/prompt_provider.dart';

class PromptEditorScreen extends StatefulWidget {
  const PromptEditorScreen({super.key, this.prompt});

  final PromptItem? prompt;

  @override
  State<PromptEditorScreen> createState() => _PromptEditorScreenState();
}

class _PromptEditorScreenState extends State<PromptEditorScreen> {
  final _formKey = GlobalKey<FormState>();
  late final TextEditingController _titleController;
  late final TextEditingController _contentController;
  late final TextEditingController _tagsController;
  late String _selectedCategory;

  @override
  void initState() {
    super.initState();
    _titleController = TextEditingController(text: widget.prompt?.title ?? '');
    _contentController = TextEditingController(text: widget.prompt?.content ?? '');
    _tagsController = TextEditingController(text: widget.prompt?.tags.join(', ') ?? '');
    _selectedCategory = widget.prompt?.category ?? PromptProvider.defaultCategories.first;
  }

  @override
  void dispose() {
    _titleController.dispose();
    _contentController.dispose();
    _tagsController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final provider = context.read<PromptProvider>();

    return Scaffold(
      appBar: AppBar(title: Text(widget.prompt == null ? 'Add Prompt' : 'Edit Prompt')),
      body: Form(
        key: _formKey,
        child: ListView(
          padding: const EdgeInsets.all(16),
          children: [
            TextFormField(
              controller: _titleController,
              decoration: const InputDecoration(labelText: 'Title'),
              validator: (value) => value == null || value.trim().isEmpty ? 'Required' : null,
            ),
            const SizedBox(height: 12),
            TextFormField(
              controller: _contentController,
              minLines: 4,
              maxLines: 8,
              decoration: const InputDecoration(labelText: 'Prompt Content'),
              validator: (value) => value == null || value.trim().isEmpty ? 'Required' : null,
            ),
            const SizedBox(height: 12),
            DropdownButtonFormField<String>(
              value: _selectedCategory,
              items: PromptProvider.defaultCategories
                  .map((c) => DropdownMenuItem(value: c, child: Text(c)))
                  .toList(),
              onChanged: (value) => setState(() => _selectedCategory = value!),
              decoration: const InputDecoration(labelText: 'Category'),
            ),
            const SizedBox(height: 12),
            TextFormField(
              controller: _tagsController,
              decoration: const InputDecoration(labelText: 'Tags (comma separated)'),
            ),
            const SizedBox(height: 20),
            FilledButton(
              onPressed: () async {
                if (!_formKey.currentState!.validate()) return;

                final tags = _tagsController.text
                    .split(',')
                    .map((t) => t.trim())
                    .where((t) => t.isNotEmpty)
                    .toList();

                final draft = PromptItem(
                  id: widget.prompt?.id,
                  title: _titleController.text.trim(),
                  content: _contentController.text.trim(),
                  category: _selectedCategory,
                  tags: tags,
                  createdAt: widget.prompt?.createdAt ?? DateTime.now(),
                  favorite: widget.prompt?.favorite ?? false,
                  usageCount: widget.prompt?.usageCount ?? 0,
                  lastUsedAt: widget.prompt?.lastUsedAt,
                );

                if (widget.prompt == null) {
                  await provider.addPrompt(draft);
                } else {
                  await provider.updatePrompt(draft);
                }

                if (context.mounted) {
                  Navigator.pop(context);
                }
              },
              child: const Text('Save Prompt'),
            ),
          ],
        ),
      ),
    );
  }
}
