import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import 'providers/prompt_provider.dart';
import 'screens/home_screen.dart';

void main() {
  runApp(const PromptVaultApp());
}

class PromptVaultApp extends StatelessWidget {
  const PromptVaultApp({super.key});

  @override
  Widget build(BuildContext context) {
    return ChangeNotifierProvider(
      create: (_) => PromptProvider(),
      child: MaterialApp(
        title: 'Prompt Vault',
        debugShowCheckedModeBanner: false,
        themeMode: ThemeMode.system,
        theme: ThemeData(
          useMaterial3: true,
          colorSchemeSeed: Colors.indigo,
          brightness: Brightness.light,
        ),
        darkTheme: ThemeData(
          useMaterial3: true,
          colorSchemeSeed: Colors.indigo,
          brightness: Brightness.dark,
        ),
        home: const HomeScreen(),
      ),
    );
  }
}
