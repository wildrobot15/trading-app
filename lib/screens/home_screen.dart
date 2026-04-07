import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../models/prompt_item.dart';
import '../providers/prompt_provider.dart';
import '../widgets/prompt_card.dart';
import 'prompt_editor_screen.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  int _tabIndex = 0;

  @override
  Widget build(BuildContext context) {
    return Consumer<PromptProvider>(
      builder: (context, provider, _) {
        final titles = ['All Prompts', 'Categories', 'Favorites'];

        return Scaffold(
          appBar: AppBar(
            title: Text(titles[_tabIndex]),
            actions: [
              IconButton(
                icon: const Icon(Icons.download),
                onPressed: () async {
                  final json = await provider.exportPrompts();
                  if (!context.mounted) return;
                  showDialog<void>(
                    context: context,
                    builder: (_) => AlertDialog(
                      title: const Text('Export JSON'),
                      content: SingleChildScrollView(child: SelectableText(json)),
                    ),
                  );
                },
              ),
            ],
          ),
          body: Column(
            children: [
              Padding(
                padding: const EdgeInsets.all(12),
                child: TextField(
                  decoration: const InputDecoration(
                    hintText: 'Search prompts, tags, keywords...',
                    prefixIcon: Icon(Icons.search),
                  ),
                  onChanged: provider.setQuery,
                ),
              ),
              if (_tabIndex == 1)
                SizedBox(
                  height: 52,
                  child: ListView(
                    scrollDirection: Axis.horizontal,
                    padding: const EdgeInsets.symmetric(horizontal: 12),
                    children: [
                      FilterChip(
                        selected: false,
                        label: const Text('All'),
                        onSelected: (_) => provider.setCategoryFilter('All'),
                      ),
                      const SizedBox(width: 8),
                      ...PromptProvider.defaultCategories.map(
                        (category) => Padding(
                          padding: const EdgeInsets.only(right: 8),
                          child: FilterChip(
                            selected: false,
                            label: Text(category),
                            onSelected: (_) => provider.setCategoryFilter(category),
                          ),
                        ),
                      ),
                    ],
                  ),
                ),
              Expanded(child: _buildBody(provider)),
            ],
          ),
          floatingActionButton: FloatingActionButton(
            onPressed: () {
              Navigator.push(
                context,
                MaterialPageRoute(builder: (_) => const PromptEditorScreen()),
              );
            },
            child: const Icon(Icons.add),
          ),
          bottomNavigationBar: NavigationBar(
            selectedIndex: _tabIndex,
            onDestinationSelected: (index) {
              setState(() => _tabIndex = index);
              if (index == 2) {
                provider.setFavoriteOnly(true);
              } else {
                provider.setFavoriteOnly(false);
              }
            },
            destinations: const [
              NavigationDestination(icon: Icon(Icons.home), label: 'Home'),
              NavigationDestination(icon: Icon(Icons.folder), label: 'Categories'),
              NavigationDestination(icon: Icon(Icons.favorite), label: 'Favorites'),
            ],
          ),
        );
      },
    );
  }

  Widget _buildBody(PromptProvider provider) {
    final list = provider.filteredPrompts;
    return ListView(
      children: [
        _section('Recently Used', provider.recentPrompts),
        _section('Most Used', provider.mostUsedPrompts),
        const Padding(
          padding: EdgeInsets.fromLTRB(16, 8, 16, 6),
          child: Text('All'),
        ),
        if (list.isEmpty)
          const Padding(
            padding: EdgeInsets.all(18),
            child: Text('No prompts found.'),
          )
        else
          ...list.map(
            (prompt) => PromptCard(
              prompt: prompt,
              onEdit: () {
                Navigator.push(
                  context,
                  MaterialPageRoute(
                    builder: (_) => PromptEditorScreen(prompt: prompt),
                  ),
                );
              },
            ),
          ),
      ],
    );
  }

  Widget _section(String title, List<PromptItem> prompts) {
    if (prompts.isEmpty) return const SizedBox.shrink();

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Padding(
          padding: const EdgeInsets.fromLTRB(16, 10, 16, 6),
          child: Text(title, style: const TextStyle(fontWeight: FontWeight.w600)),
        ),
        ...prompts.take(3).map((prompt) => PromptCard(prompt: prompt)),
      ],
    );
  }
}
