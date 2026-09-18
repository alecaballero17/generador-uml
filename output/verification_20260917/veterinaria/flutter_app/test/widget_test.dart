import 'package:flutter_test/flutter_test.dart';
import 'package:flutter/material.dart';
import 'package:sistema_veterinaria/main.dart';

void main() {
  testWidgets('Carga inicial de la aplicación Sistema Veterinaria', (WidgetTester tester) async {
    await tester.pumpWidget(const UMLGeneratedApp());
    expect(find.byType(MaterialApp), findsOneWidget);
  });
}
