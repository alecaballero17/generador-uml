import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import '../services/api_config.dart';
__IMPORTS__

class _Module {
  final String name, endpoint;
  final IconData icon;
  final WidgetBuilder list, form;
  const _Module(this.name, this.endpoint, this.icon, this.list, this.form);
}
class DashboardScreen extends StatefulWidget {
  final VoidCallback onToggleTheme;
  const DashboardScreen({super.key, required this.onToggleTheme});
  @override
  State<DashboardScreen> createState() => _DashboardScreenState();
}
class _DashboardScreenState extends State<DashboardScreen> {
  final List<_Module> _modules = [__MODULES__];
  final _search = TextEditingController();
  final _url = TextEditingController(text: ApiConfig.baseUrl);
  final Map<String, int> _counts = {};
  int _tab = 0;
  bool? _online;
  bool _checking = false, _savingUrl = false;
  String? _connectionError;
  @override
  void initState() { super.initState(); _refresh(); }
  @override
  void dispose() { _url.dispose(); _search.dispose(); super.dispose(); }
  Future<void> _refresh() async {
    if (_checking) return;
    setState(() { _checking = true; _connectionError = null; });
    final online = await ApiConfig.checkConnection();
    final counts = <String, int>{};
    if (online) {
      await Future.wait(_modules.map((module) async {
        try {
          final response = await http.get(Uri.parse('${ApiConfig.baseUrl}/${module.endpoint}/count'), headers: ApiConfig.headers).timeout(ApiConfig.timeoutDuration);
          if (response.statusCode == 200) {
            final body = jsonDecode(response.body);
            if (body['count'] is num) counts[module.endpoint] = (body['count'] as num).toInt();
          }
        } catch (_) { /* Unknown counts stay unknown instead of showing a false zero. */ }
      }));
    }
    if (!mounted) return;
    setState(() { _online = online; _checking = false; _counts..clear()..addAll(counts); });
  }
  Future<void> _open(_Module module, {bool create = false}) async {
    await Navigator.push(context, MaterialPageRoute(builder: create ? module.form : module.list));
    if (mounted) _refresh();
  }
  void _newRecord() {
    showModalBottomSheet(context: context, showDragHandle: true, isScrollControlled: true, builder: (ctx) => SafeArea(child: SingleChildScrollView(child: Padding(
      padding: const EdgeInsets.fromLTRB(20, 0, 20, 24), child: Column(mainAxisSize: MainAxisSize.min, crossAxisAlignment: CrossAxisAlignment.start, children: [
        const Text('¿Qué quieres registrar?', style: TextStyle(fontSize: 22, fontWeight: FontWeight.w700)),
        const SizedBox(height: 6), const Text('Elige una sección para empezar.'), const SizedBox(height: 16),
        for (final module in _modules) ListTile(leading: Icon(module.icon, color: Theme.of(ctx).colorScheme.primary), title: Text(module.name), trailing: const Icon(Icons.add_rounded), onTap: () { Navigator.pop(ctx); _open(module, create: true); }),
      ]),
    ))));
  }
  Future<void> _saveConnection() async {
    setState(() { _savingUrl = true; _connectionError = null; });
    try {
      await ApiConfig.setBaseUrl(_url.text);
      await _refresh();
      if (mounted && _online != true) setState(() => _connectionError = 'No hay respuesta. Comprueba que el servidor esté encendido y el teléfono conectado.');
    } catch (error) { if (mounted) setState(() => _connectionError = error.toString()); }
    finally { if (mounted) setState(() => _savingUrl = false); }
  }
  Widget _connectionChip() {
    final color = _checking ? Theme.of(context).colorScheme.primary : _online == true ? const Color(0xFF73D5B4) : const Color(0xFFE0B97C);
    return ActionChip(avatar: _checking ? SizedBox(width: 13, height: 13, child: CircularProgressIndicator(strokeWidth: 2, color: color)) : Icon(_online == true ? Icons.check_circle_outline : Icons.wifi_off_rounded, size: 16, color: color),
      label: Text(_checking ? 'Conectando' : _online == true ? 'Conectado' : 'Sin conexión', style: const TextStyle(fontSize: 11)), onPressed: () => setState(() => _tab = 2), padding: const EdgeInsets.symmetric(horizontal: 2), side: BorderSide(color: color.withOpacity(.25)), backgroundColor: color.withOpacity(.08));
  }
  Widget _metric(String value, String label, IconData icon) => Expanded(child: Column(children: [
    Icon(icon, size: 19, color: Theme.of(context).colorScheme.primary), const SizedBox(height: 7), Text(value, style: const TextStyle(fontSize: 23, fontWeight: FontWeight.w700)), const SizedBox(height: 2), Text(label, style: TextStyle(fontSize: 11, color: Theme.of(context).colorScheme.onSurface.withOpacity(.6))),
  ]));
  Widget _moduleCard(_Module module, int index) {
    final scheme = Theme.of(context).colorScheme;
    final colors = [scheme.primary, const Color(0xFF70C8B1), const Color(0xFFE0B77C), const Color(0xFF93B6E9)];
    final color = colors[index % colors.length];
    final count = _counts[module.endpoint];
    return Card(child: InkWell(borderRadius: BorderRadius.circular(20), onTap: () => _open(module), child: Padding(padding: const EdgeInsets.all(17), child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
      Row(children: [Container(padding: const EdgeInsets.all(10), decoration: BoxDecoration(color: color.withOpacity(.13), borderRadius: BorderRadius.circular(13)), child: Icon(module.icon, color: color, size: 23)), const Spacer(), Icon(Icons.north_east_rounded, size: 17, color: scheme.onSurface.withOpacity(.4))]),
      const SizedBox(height: 19), Text(module.name, maxLines: 2, overflow: TextOverflow.ellipsis, style: const TextStyle(fontSize: 17, fontWeight: FontWeight.w700)), const SizedBox(height: 4),
      Text(count == null ? 'Abrir registros' : '$count ${count == 1 ? "registro" : "registros"}', style: TextStyle(fontSize: 12, color: scheme.onSurface.withOpacity(.6))),
    ]))));
  }
  Widget _home() {
    final scheme = Theme.of(context).colorScheme;
    final totalKnown = _counts.length == _modules.length && _online == true;
    final total = _counts.values.fold<int>(0, (a,b) => a+b);
    return RefreshIndicator(onRefresh: _refresh, child: ListView(padding: const EdgeInsets.fromLTRB(22, 8, 22, 28), children: [
      Text('TU GESTIÓN, MÁS SIMPLE', style: TextStyle(color: scheme.primary, fontSize: 10, fontWeight: FontWeight.w700, letterSpacing: 2)),
      const SizedBox(height: 12), const Text('Todo bajo\ncontrol.', style: TextStyle(fontSize: 39, height: 1.12, fontWeight: FontWeight.w800, letterSpacing: -1.4)), const SizedBox(height: 10),
      Text('Consulta, registra y organiza en un solo lugar.', style: TextStyle(fontSize: 13, color: scheme.onSurface.withOpacity(.6))), const SizedBox(height: 24),
      Container(padding: const EdgeInsets.all(22), decoration: BoxDecoration(gradient: const LinearGradient(colors: [Color(0xFF423261), Color(0xFF65508C)]), borderRadius: BorderRadius.circular(23)), child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        const Row(children: [Icon(Icons.space_dashboard_outlined, color: Color(0xFFD6C6F2), size: 20), SizedBox(width: 9), Text('TU APLICACIÓN', style: TextStyle(color: Color(0xFFD6C6F2), fontSize: 10, letterSpacing: 1.5))]),
        const SizedBox(height: 15), Text(__TITLE__, style: const TextStyle(color: Colors.white, fontSize: 23, fontWeight: FontWeight.w700)), const SizedBox(height: 5),
        const Text('Empieza por lo que necesitas hacer hoy.', style: TextStyle(color: Color(0xFFDAD1EC), fontSize: 12)), const SizedBox(height: 20),
        FilledButton.icon(style: FilledButton.styleFrom(backgroundColor: const Color(0xFFF0E6FF), foregroundColor: const Color(0xFF483267), minimumSize: const Size(double.infinity, 48)), onPressed: _newRecord, icon: const Icon(Icons.add_rounded, size: 20), label: const Text('Nuevo registro')),
      ])), const SizedBox(height: 23),
      Row(children: [_metric('${_modules.length}', 'Secciones', Icons.grid_view_rounded), _metric(totalKnown ? '$total' : '—', 'Registros', Icons.layers_outlined)]),
      const SizedBox(height: 22), Row(children: [const Expanded(child: Text('Explora tu aplicación', style: TextStyle(fontSize: 18, fontWeight: FontWeight.w700))), TextButton(onPressed: () => setState(() => _tab = 1), child: const Text('Ver todo'))]), const SizedBox(height: 8),
      LayoutBuilder(builder: (ctx, box) {
        final wideText = MediaQuery.textScalerOf(ctx).scale(16) > 21;
        final columns = box.maxWidth < 290 || wideText ? 1 : box.maxWidth > 650 ? 3 : 2;
        return Wrap(spacing: 12, runSpacing: 12, children: [for (int i = 0; i < _modules.length; i++) SizedBox(width: (box.maxWidth - 12*(columns-1))/columns, child: _moduleCard(_modules[i], i))]);
      }),
      if (_online == false) Padding(padding: const EdgeInsets.only(top: 20), child: TextButton.icon(onPressed: () => setState(() => _tab = 2), icon: const Icon(Icons.link_rounded, size: 17), label: const Text('Conecta el servidor para guardar cambios'))),
    ]));
  }
  Widget _records() {
    final query = _search.text.trim().toLowerCase();
    final modules = _modules.where((m) => m.name.toLowerCase().contains(query)).toList();
    return ListView(padding: const EdgeInsets.all(22), children: [
      const Text('Tus registros', style: TextStyle(fontSize: 29, fontWeight: FontWeight.w700)), const SizedBox(height: 8), const Text('Elige una sección para consultar o agregar información.'), const SizedBox(height: 22),
      TextField(controller: _search, onChanged: (_) => setState(() {}), decoration: const InputDecoration(prefixIcon: Icon(Icons.search_rounded), hintText: 'Buscar una sección')), const SizedBox(height: 20),
      if (modules.isEmpty) const Padding(padding: EdgeInsets.all(24), child: Text('No hay secciones con ese nombre.')),
      for (final module in modules) Padding(padding: const EdgeInsets.only(bottom: 12), child: Card(child: ListTile(leading: Icon(module.icon, color: Theme.of(context).colorScheme.primary), title: Text(module.name, style: const TextStyle(fontWeight: FontWeight.w700)), subtitle: Text(_counts[module.endpoint] == null ? 'Ver registros' : '${_counts[module.endpoint]} registros'), trailing: const Icon(Icons.chevron_right_rounded), onTap: () => _open(module)))),
    ]);
  }
  Widget _settings() => ListView(padding: const EdgeInsets.all(22), children: [
    const Text('Ajustes', style: TextStyle(fontSize: 29, fontWeight: FontWeight.w700)), const SizedBox(height: 8), const Text('Personaliza la aplicación y su conexión.'), const SizedBox(height: 25),
    Card(child: ListTile(leading: const Icon(Icons.dark_mode_outlined), title: const Text('Apariencia'), subtitle: Text(Theme.of(context).brightness == Brightness.dark ? 'Modo oscuro' : 'Modo claro'), trailing: Switch(value: Theme.of(context).brightness == Brightness.dark, onChanged: (_) => widget.onToggleTheme()))), const SizedBox(height: 18),
    Card(child: Padding(padding: const EdgeInsets.all(20), child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
      const Row(children: [Icon(Icons.link_rounded), SizedBox(width: 10), Text('Conexión', style: TextStyle(fontSize: 18, fontWeight: FontWeight.w700))]), const SizedBox(height: 12),
      Text(_checking ? 'Comprobando conexión…' : _online == true ? 'Conectado. Ya puedes gestionar tus registros.' : 'El servidor no responde. Puedes consultar la información guardada previamente, pero necesitas conexión para guardar cambios.', style: const TextStyle(fontSize: 13)), const SizedBox(height: 20),
      TextField(controller: _url, keyboardType: TextInputType.url, autocorrect: false, decoration: const InputDecoration(labelText: 'Dirección del servidor', hintText: 'https://servidor/api', prefixIcon: Icon(Icons.dns_outlined))),
      if (_connectionError != null) Padding(padding: const EdgeInsets.only(top: 12), child: Text(_connectionError!, style: TextStyle(color: Theme.of(context).colorScheme.error))),
      const SizedBox(height: 16), SizedBox(width: double.infinity, child: FilledButton.icon(onPressed: _savingUrl || _checking ? null : _saveConnection, icon: const Icon(Icons.sync_rounded), label: Text(_savingUrl ? 'Conectando…' : 'Guardar y conectar'))),
      const SizedBox(height: 12), ExpansionTile(tilePadding: EdgeInsets.zero, title: const Text('Ayuda para conectar', style: TextStyle(fontSize: 13)), children: [
        const Padding(padding: EdgeInsets.only(bottom: 14), child: Text('Por USB: conecta el teléfono a la computadora y mantén el backend en ejecución. Por Wi-Fi: usa la dirección de la computadora en la misma red.', style: TextStyle(fontSize: 12))),
        Wrap(spacing: 8, children: [ActionChip(label: const Text('USB · puerto 8087'), onPressed: () => _url.text = 'http://127.0.0.1:8087/api'), ActionChip(label: const Text('Emulador · 8080'), onPressed: () => _url.text = 'http://10.0.2.2:8080/api')]),
      ]),
    ]))),
  ]);
  @override
  Widget build(BuildContext context) => Scaffold(
    appBar: AppBar(title: const Text(__TITLE__, maxLines: 1, overflow: TextOverflow.ellipsis), actions: [Padding(padding: const EdgeInsets.only(right: 16), child: _connectionChip())]),
    body: SafeArea(top: false, child: _tab == 0 ? _home() : _tab == 1 ? _records() : _settings()),
    bottomNavigationBar: NavigationBar(selectedIndex: _tab, onDestinationSelected: (index) => setState(() => _tab = index), destinations: const [NavigationDestination(icon: Icon(Icons.grid_view_outlined), selectedIcon: Icon(Icons.grid_view_rounded), label: 'Inicio'), NavigationDestination(icon: Icon(Icons.layers_outlined), selectedIcon: Icon(Icons.layers_rounded), label: 'Registros'), NavigationDestination(icon: Icon(Icons.tune_rounded), label: 'Ajustes')]),
  );
}
