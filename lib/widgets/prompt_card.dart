import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import 'package:provider/provider.dart';

import '../models/prompt_item.dart';
import '../providers/prompt_provider.dart';

class PromptCard extends StatelessWidget {
  const PromptCard({
    super.key,
    required this.prompt,
    this.onEdit,
  });

  final PromptItem prompt;
  final VoidCallback? onEdit;

  @override
  Widget build(BuildContext context) {
    final provider = context.read<PromptProvider>();

    return Card(
      margin: const EdgeInsets.symmetric(vertical: 6, horizontal: 12),
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Expanded(
                  child: Text(
                    prompt.title,
                    style: Theme.of(context).textTheme.titleMedium,
                  ),
                ),
                IconButton(
                  icon: Icon(
                    prompt.favorite ? Icons.favorite : Icons.favorite_border,
                    color: prompt.favorite ? Colors.red : null,
                  ),
                  onPressed: () => provider.toggleFavorite(prompt),
                ),
              ],
            ),
            const SizedBox(height: 8),
            Text(prompt.content, maxLines: 4, overflow: TextOverflow.ellipsis),
            const SizedBox(height: 8),
            Wrap(
              spacing: 6,
              runSpacing: 6,
              children: [
                Chip(label: Text(prompt.category)),
                ...prompt.tags.map((tag) => Chip(label: Text('#$tag'))),
              ],
            ),
            const SizedBox(height: 8),
            Text(
              'Created: ${DateFormat('yyyy-MM-dd').format(prompt.createdAt)} • Used: ${prompt.usageCount}',
              style: Theme.of(context).textTheme.bodySmall,
            ),
            const SizedBox(height: 8),
            Row(
              children: [
                FilledButton.icon(
                  onPressed: () => provider.copyPrompt(prompt),
                  icon: const Icon(Icons.copy),
                  label: const Text('Copy'),
                ),
                const SizedBox(width: 8),
                OutlinedButton.icon(
                  onPressed: () => provider.sharePrompt(prompt),
                  icon: const Icon(Icons.share),
                  label: const Text('Share'),
                ),
                const Spacer(),
                IconButton(onPressed: onEdit, icon: const Icon(Icons.edit)),
                IconButton(
                  onPressed: () => provider.deletePrompt(prompt.id!),
                  icon: const Icon(Icons.delete),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}
