import json
import random
import uuid
from functools import wraps
from django.http import JsonResponse
from django.utils import functional
from django.utils.text import slugify
from django.urls import reverse
from django.db.models import Q
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import Locations, Npc, Monsters_All_db, Monsters_Active, Items_All_db, Items_Active, Kronika, DmNote
from player_site_app.models import (
    Player, Char_info, Logs, Achivements_database, Achivements_players,
    CharacterSpellSlot, CharacterFeature
)
from player_site_app.achivements import zbohatlik_ach, smrtici_stroj_ach
from dnd_atarax.terminal import (
    log_dm, log_arena, log_hp, log_mob, log_player,
    log_gold, log_success, log_warning, log_error, log_info
)
from .loot import loot_gold, loot_items, loot_temna_esence

def dm_required(view_func):
    """
    Dekorátor pro DM sekci.
    Kontroluje:
    1) Zda je uživatel přihlášený (request.user.is_authenticated)
    2) Zda má administrátorská / staff práva (request.user.is_staff=True)
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        # 1. Kontrola přihlášení
        if not request.user.is_authenticated:
            log_warning("Neautorizovaný přístup do DM sekce", f"Nepřihlášený požadavek na '{request.path}'")
            return redirect('player_site_app:index')

        # 2. Kontrola administrátorských práv
        if not request.user.is_staff:
            log_warning("Nedostatečná oprávnění", f"Uživatel '{request.user.username}' nemá staff práva pro '{request.path}'")
            messages.error(request, "Pro přístup do DM sekce musíte mít administrátorská práva (is_staff).")
            return redirect('player_site_app:prehled_postav')

        return view_func(request, *args, **kwargs)
    return _wrapped_view

@dm_required
def index(request):
    """Sjednocený rozcestník DM - Nástroje"""
    return redirect('dm_site_app:tools')

@dm_required
def tools(request):
    """2. Nástroje DM"""
    return render(request, 'dm_site_app/tools.html', {
        'current_page': 'tools',
    })

# ==========================================
# 3. NPC MANAGEMENT
# ==========================================

@dm_required
def npc(request):
    """Přehled všech NPC s vyhledáváním a filtrací podle lokace."""
    q = request.GET.get('q', '').strip()
    loc_id = request.GET.get('location', '').strip()

    qs = Npc.objects.select_related('location').all()
    if q:
        qs = qs.filter(Q(name__icontains=q) | Q(description__icontains=q))
    if loc_id:
        qs = qs.filter(location_id=loc_id)

    all_locations = Locations.objects.all().order_by('name')
    context = {
        'npcs': qs,
        'locations': all_locations,
        'selected_location': loc_id,
        'search_query': q,
        'current_page': 'npc',
    }
    return render(request, 'dm_site_app/npc.html', context)

# Zpětná kompatibilita pro název funkce npcs
npcs = npc

@dm_required
def npc_detail(request, npc_id):
    """Detail konkrétního NPC se všemi informacemi a možnostmi správy."""
    npc_obj = get_object_or_404(Npc.objects.select_related('location'), id=npc_id)
    return render(request, 'dm_site_app/npc_detail.html', {
        'npc_obj': npc_obj,
        'current_page': 'npc',
    })

@dm_required
def npc_create(request):
    """Vytvoření nového NPC."""
    all_locations = Locations.objects.all().order_by('name')

    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        location_id = request.POST.get('location') or None
        gender = request.POST.get('gender') or None
        description = request.POST.get('description', '').strip()
        image_url = request.POST.get('image_url', '').strip() or None
        uploaded_image = request.FILES.get('image')

        try:
            loot_gold = int(request.POST.get('loot_gold', 0) or 0)
        except (ValueError, TypeError):
            loot_gold = 0

        try:
            loot_silver = int(request.POST.get('loot_silver', 0) or 0)
        except (ValueError, TypeError):
            loot_silver = 0

        loot_able = request.POST.get('loot_able') in ('on', 'true', '1')
        is_dead = request.POST.get('is_dead') in ('on', 'true', '1')
        in_fight = request.POST.get('in_fight') in ('on', 'true', '1')

        if not name:
            messages.error(request, "Jméno NPC je povinné.")
            return render(request, 'dm_site_app/npc_form.html', {
                'locations': all_locations,
                'is_edit': False,
                'current_page': 'npc',
            })

        loc_instance = None
        if location_id:
            loc_instance = Locations.objects.filter(id=location_id).first()

        npc_obj = Npc.objects.create(
            name=name,
            location=loc_instance,
            gender=gender,
            description=description,
            image=uploaded_image,
            image_url=image_url,
            loot_gold=loot_gold,
            loot_silver=loot_silver,
            loot_able=loot_able,
            is_dead=is_dead,
            in_fight=in_fight
        )

        log_dm("Vytvořeno nové NPC", f"'{name}' (ID: {npc_obj.id})")
        messages.success(request, f"Nové NPC '{name}' bylo úspěšně vytvořeno.")
        return redirect('dm_site_app:npc_detail', npc_id=npc_obj.id)

    return render(request, 'dm_site_app/npc_form.html', {
        'locations': all_locations,
        'is_edit': False,
        'current_page': 'npc',
    })

@dm_required
def npc_edit(request, npc_id):
    """Úprava existujícího NPC včetně nahrání/změny obrázku."""
    npc_obj = get_object_or_404(Npc, id=npc_id)
    all_locations = Locations.objects.all().order_by('name')

    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        location_id = request.POST.get('location') or None
        gender = request.POST.get('gender') or None
        description = request.POST.get('description', '').strip()
        image_url = request.POST.get('image_url', '').strip() or None
        uploaded_image = request.FILES.get('image')
        remove_image = request.POST.get('remove_image') in ('on', 'true', '1')

        try:
            loot_gold = int(request.POST.get('loot_gold', 0) or 0)
        except (ValueError, TypeError):
            loot_gold = 0

        try:
            loot_silver = int(request.POST.get('loot_silver', 0) or 0)
        except (ValueError, TypeError):
            loot_silver = 0

        loot_able = request.POST.get('loot_able') in ('on', 'true', '1')
        is_dead = request.POST.get('is_dead') in ('on', 'true', '1')
        in_fight = request.POST.get('in_fight') in ('on', 'true', '1')

        if not name:
            messages.error(request, "Jméno NPC je povinné.")
            return render(request, 'dm_site_app/npc_form.html', {
                'npc_obj': npc_obj,
                'locations': all_locations,
                'is_edit': True,
                'current_page': 'npc',
            })

        loc_instance = None
        if location_id:
            loc_instance = Locations.objects.filter(id=location_id).first()

        npc_obj.name = name
        npc_obj.location = loc_instance
        npc_obj.gender = gender
        npc_obj.description = description
        npc_obj.loot_gold = loot_gold
        npc_obj.loot_silver = loot_silver
        npc_obj.loot_able = loot_able
        npc_obj.is_dead = is_dead
        npc_obj.in_fight = in_fight

        if remove_image:
            if npc_obj.image:
                npc_obj.image.delete(save=False)
            npc_obj.image = None
            npc_obj.image_url = None
        elif uploaded_image:
            if npc_obj.image:
                npc_obj.image.delete(save=False)
            npc_obj.image = uploaded_image
            npc_obj.image_url = None
        elif image_url:
            npc_obj.image_url = image_url

        npc_obj.save()
        log_dm("Upraveno NPC", f"'{name}' (ID: {npc_obj.id})")
        messages.success(request, f"Záznam NPC '{name}' byl úspěšně upraven.")
        return redirect('dm_site_app:npc_detail', npc_id=npc_obj.id)

    return render(request, 'dm_site_app/npc_form.html', {
        'npc_obj': npc_obj,
        'locations': all_locations,
        'is_edit': True,
        'current_page': 'npc',
    })

@dm_required
def npc_delete(request, npc_id):
    """Smazání NPC."""
    npc_obj = get_object_or_404(Npc, id=npc_id)
    if request.method == 'POST':
        name = npc_obj.name or "Neznámé NPC"
        if npc_obj.image:
            npc_obj.image.delete(save=False)
        npc_obj.delete()
        log_dm("Smazáno NPC", f"'{name}' (ID: {npc_id})")
        messages.success(request, f"NPC '{name}' bylo smazáno.")
        return redirect('dm_site_app:npc')
    return redirect('dm_site_app:npc_detail', npc_id=npc_id)


# ==========================================
# 4. LOCATIONS MANAGEMENT
# ==========================================

@dm_required
def locations(request):
    """Přehled všech herních lokací s vyhledáváním a filtrováním dle typu."""
    q = request.GET.get('q', '').strip()
    loc_type = request.GET.get('type', '').strip()

    qs = Locations.objects.select_related('layer_up', 'layer_down').prefetch_related('npcs').all()
    if q:
        qs = qs.filter(Q(name__icontains=q) | Q(description__icontains=q))
    if loc_type:
        qs = qs.filter(type=loc_type)

    context = {
        'locations': qs,
        'type_choices': Locations.type_choices,
        'selected_type': loc_type,
        'search_query': q,
        'current_page': 'locations',
    }
    return render(request, 'dm_site_app/locations.html', context)

@dm_required
def location_detail(request, loc_id):
    """Detail lokace s mapou, hierarchií a seznamem NPC v ní."""
    location_obj = get_object_or_404(
        Locations.objects.select_related('layer_up', 'layer_down').prefetch_related('npcs', 'locations_below', 'locations_above'),
        id=loc_id
    )
    return render(request, 'dm_site_app/location_detail.html', {
        'location_obj': location_obj,
        'current_page': 'locations',
    })

@dm_required
def location_create(request):
    """Vytvoření nové herní lokace."""
    all_locations = Locations.objects.all().order_by('name')

    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        loc_type = request.POST.get('type') or None
        description = request.POST.get('description', '').strip()
        layer_up_id = request.POST.get('layer_up') or None
        layer_down_id = request.POST.get('layer_down') or None
        image_url = request.POST.get('image_url', '').strip() or None
        uploaded_image = request.FILES.get('image')

        if not name:
            messages.error(request, "Název lokace je povinný.")
            return render(request, 'dm_site_app/location_form.html', {
                'locations': all_locations,
                'type_choices': Locations.type_choices,
                'is_edit': False,
                'current_page': 'locations',
            })

        layer_up_obj = Locations.objects.filter(id=layer_up_id).first() if layer_up_id else None
        layer_down_obj = Locations.objects.filter(id=layer_down_id).first() if layer_down_id else None

        loc_obj = Locations.objects.create(
            name=name,
            type=loc_type,
            description=description,
            layer_up=layer_up_obj,
            layer_down=layer_down_obj,
            image=uploaded_image,
            image_url=image_url
        )

        log_dm("Vytvořena nová lokace", f"'{name}' (ID: {loc_obj.id})")
        messages.success(request, f"Lokace '{name}' byla úspěšně vytvořena.")
        return redirect('dm_site_app:location_detail', loc_id=loc_obj.id)

    return render(request, 'dm_site_app/location_form.html', {
        'locations': all_locations,
        'type_choices': Locations.type_choices,
        'is_edit': False,
        'current_page': 'locations',
    })

@dm_required
def location_edit(request, loc_id):
    """Úprava existující herní lokace včetně mapy."""
    location_obj = get_object_or_404(Locations, id=loc_id)
    all_locations = Locations.objects.exclude(id=loc_id).order_by('name')

    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        loc_type = request.POST.get('type') or None
        description = request.POST.get('description', '').strip()
        layer_up_id = request.POST.get('layer_up') or None
        layer_down_id = request.POST.get('layer_down') or None
        image_url = request.POST.get('image_url', '').strip() or None
        uploaded_image = request.FILES.get('image')
        remove_image = request.POST.get('remove_image') in ('on', 'true', '1')

        if not name:
            messages.error(request, "Název lokace je povinný.")
            return render(request, 'dm_site_app/location_form.html', {
                'location_obj': location_obj,
                'locations': all_locations,
                'type_choices': Locations.type_choices,
                'is_edit': True,
                'current_page': 'locations',
            })

        layer_up_obj = Locations.objects.filter(id=layer_up_id).first() if layer_up_id else None
        layer_down_obj = Locations.objects.filter(id=layer_down_id).first() if layer_down_id else None

        location_obj.name = name
        location_obj.type = loc_type
        location_obj.description = description
        location_obj.layer_up = layer_up_obj
        location_obj.layer_down = layer_down_obj

        if remove_image:
            if location_obj.image:
                location_obj.image.delete(save=False)
            location_obj.image = None
            location_obj.image_url = None
        elif uploaded_image:
            if location_obj.image:
                location_obj.image.delete(save=False)
            location_obj.image = uploaded_image
            location_obj.image_url = None
        elif image_url:
            location_obj.image_url = image_url

        location_obj.save()
        log_dm("Upravena lokace", f"'{name}' (ID: {location_obj.id})")
        messages.success(request, f"Lokace '{name}' byla úspěšně upravena.")
        return redirect('dm_site_app:location_detail', loc_id=location_obj.id)

    return render(request, 'dm_site_app/location_form.html', {
        'location_obj': location_obj,
        'locations': all_locations,
        'type_choices': Locations.type_choices,
        'is_edit': True,
        'current_page': 'locations',
    })

@dm_required
def location_delete(request, loc_id):
    """Smazání herní lokace."""
    location_obj = get_object_or_404(Locations, id=loc_id)
    if request.method == 'POST':
        name = location_obj.name
        if location_obj.image:
            location_obj.image.delete(save=False)
        location_obj.delete()
        log_dm("Smazána lokace", f"'{name}' (ID: {loc_id})")
        messages.success(request, f"Lokace '{name}' byla smazána.")
        return redirect('dm_site_app:locations')
    return redirect('dm_site_app:location_detail', loc_id=loc_id)


# ==========================================
# 5. DM NOTES (POZNÁMKY PÁNA JESKYNĚ)
# ==========================================

@dm_required
def notes(request, note_id=None):
    """Přehled a čtečka poznámek DM. Aktuální poznámky jsou vždy na vrcholu."""
    q = request.GET.get('q', '').strip()
    cat = request.GET.get('category', '').strip()
    selected_id = note_id or request.GET.get('selected')

    qs = DmNote.objects.order_by('-is_current', '-updated_at')
    if q:
        qs = qs.filter(Q(title__icontains=q) | Q(content__icontains=q))
    if cat:
        qs = qs.filter(category=cat)

    categories = (
        DmNote.objects.exclude(category__isnull=True)
        .exclude(category='')
        .values_list('category', flat=True)
        .distinct()
        .order_by('category')
    )

    active_note = None
    if selected_id:
        active_note = DmNote.objects.filter(id=selected_id).first()
    if not active_note and qs.exists():
        active_note = qs.first()

    context = {
        'notes': qs,
        'active_note': active_note,
        'categories': categories,
        'selected_category': cat,
        'search_query': q,
        'current_page': 'notes',
    }
    return render(request, 'dm_site_app/notes.html', context)

@dm_required
def note_create(request):
    """Vytvoření nové poznámky s WYSIWYG editorem a klávesovými zkratkami."""
    existing_categories = (
        DmNote.objects.exclude(category__isnull=True)
        .exclude(category='')
        .values_list('category', flat=True)
        .distinct()
        .order_by('category')
    )

    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        content = request.POST.get('content', '').strip()
        category = request.POST.get('category', '').strip() or 'Kampaň'
        is_current = request.POST.get('is_current') in ('on', 'true', '1')

        if not title:
            messages.error(request, "Název poznámky je povinný.")
            return render(request, 'dm_site_app/note_form.html', {
                'categories': existing_categories,
                'is_edit': False,
                'current_page': 'notes',
            })

        note = DmNote.objects.create(
            title=title,
            content=content,
            category=category,
            is_current=is_current
        )

        log_dm("Vytvořena poznámka DM", f"'{title}' [{category}] (Aktuální: {is_current})")
        messages.success(request, f"Poznámka '{title}' byla vytvořena.")
        return redirect(f"{reverse('dm_site_app:notes')}?selected={note.id}")

    return render(request, 'dm_site_app/note_form.html', {
        'categories': existing_categories,
        'is_edit': False,
        'current_page': 'notes',
    })

@dm_required
def note_edit(request, note_id):
    """Úprava existující poznámky."""
    note = get_object_or_404(DmNote, id=note_id)
    existing_categories = (
        DmNote.objects.exclude(category__isnull=True)
        .exclude(category='')
        .values_list('category', flat=True)
        .distinct()
        .order_by('category')
    )

    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        content = request.POST.get('content', '').strip()
        category = request.POST.get('category', '').strip() or 'Kampaň'
        is_current = request.POST.get('is_current') in ('on', 'true', '1')

        if not title:
            messages.error(request, "Název poznámky je povinný.")
            return render(request, 'dm_site_app/note_form.html', {
                'note': note,
                'categories': existing_categories,
                'is_edit': True,
                'current_page': 'notes',
            })

        note.title = title
        note.content = content
        note.category = category
        note.is_current = is_current
        note.save()

        log_dm("Upravena poznámka DM", f"'{title}' [{category}]")
        messages.success(request, f"Poznámka '{title}' byla uložena.")
        return redirect(f"{reverse('dm_site_app:notes')}?selected={note.id}")

    return render(request, 'dm_site_app/note_form.html', {
        'note': note,
        'categories': existing_categories,
        'is_edit': True,
        'current_page': 'notes',
    })

@dm_required
def note_toggle_current(request, note_id):
    """Přepnutí statusu 'aktuální' (připnutí na vrchol)."""
    note = get_object_or_404(DmNote, id=note_id)
    note.is_current = not note.is_current
    note.save()

    stav = "označena jako aktuální (připnuta nahoře)" if note.is_current else "odebrána z aktuálních"
    messages.info(request, f"Poznámka '{note.title}' je nyní {stav}.")

    if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.GET.get('format') == 'json':
        return JsonResponse({'success': True, 'is_current': note.is_current})

    return redirect(f"{reverse('dm_site_app:notes')}?selected={note.id}")

@dm_required
def note_delete(request, note_id):
    """Smazání poznámky."""
    note = get_object_or_404(DmNote, id=note_id)
    if request.method == 'POST':
        title = note.title
        note.delete()
        log_dm("Smazána poznámka DM", f"'{title}' (ID: {note_id})")
        messages.success(request, f"Poznámka '{title}' byla smazána.")
        return redirect('dm_site_app:notes')
    return redirect(f"{reverse('dm_site_app:notes')}?selected={note.id}")

@dm_required
def lore(request):
    """6. Lore s možností přechodu do editace kroniky"""
    entries = Kronika.objects.all().order_by('-datum_vytvoreni')
    return render(request, 'dm_site_app/lore.html', {
        'current_page': 'lore',
        'entries': entries,
    })

@dm_required
def kronika_edit(request):
    """Správa kroniky pro Pána jeskyně: přidání záznamu, volba kategorie, odkrývání pro hráče."""
    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'add':
            nazev = request.POST.get('nazev', '').strip()
            category = request.POST.get('category', 'info')
            popis = request.POST.get('popis', '').strip()
            odkryto_hracum = (request.POST.get('odkryto_hracum') == 'on' or request.POST.get('odkryto_hracum') == 'true')

            if not nazev or not popis:
                messages.error(request, "Název i obsah záznamu musí být vyplněny.")
            else:
                entry = Kronika.objects.create(
                    nazev=nazev,
                    category=category,
                    popis=popis,
                    odkryto_hracum=odkryto_hracum
                )
                stav = "odkrytý hráčům" if odkryto_hracum else "skrytý před hráči"
                messages.success(request, f"Záznam '{nazev}' byl vytvořen a je {stav}.")
                log_dm("Vytvořen záznam v kronice", f"'{nazev}' [{category}] (odkryto: {odkryto_hracum})")

        elif action == 'toggle_reveal':
            entry_id = request.POST.get('entry_id')
            entry = get_object_or_404(Kronika, id=entry_id)
            entry.odkryto_hracum = not entry.odkryto_hracum
            entry.save()
            stav = "odkryt pro hráče" if entry.odkryto_hracum else "skryt před hráči"
            messages.info(request, f"Záznam '{entry.nazev}' je nyní {stav}.")

        elif action == 'delete':
            entry_id = request.POST.get('entry_id')
            entry = get_object_or_404(Kronika, id=entry_id)
            nazev = entry.nazev
            entry.delete()
            messages.info(request, f"Záznam '{nazev}' byl z kroniky smazán.")

        return redirect('dm_site_app:kronika_edit')

    entries = Kronika.objects.all().order_by('-datum_vytvoreni')
    return render(request, 'dm_site_app/kronika_edit.html', {
        'entries': entries,
        'current_page': 'kronika_edit',
    })

@dm_required
def golds_management(request):
    """Správa zlaťáků postav"""
    all_chars = Char_info.objects.all()
    context = {
        'all_chars': all_chars,
        'current_page': 'golds_management',
    }
    return render(request, 'dm_site_app/golds_management.html', context)

@dm_required
def add_gold(request):
    """Přidání/odebrání zlaťáků postavě"""
    if request.method == 'POST':
        char_id = request.POST.get('char_id')
        gold = request.POST.get('gold')
        silver = request.POST.get('silver')
        action = request.POST.get('action')
        plus_total_golds = round(float(gold or 0) + (float(silver or 0) / 10), 1)

        # Zapsání goldů
        if char_id:
            char = get_object_or_404(Char_info, id=char_id)
            if action == 'plus':
                char.gold += int(gold or 0)
                char.silver += int(silver or 0)
                char.total_golds += plus_total_golds
                zbohatlik_ach(char_id, plus_total_golds)  # kontrola achievementu
                log_gold(f"+{gold or 0} gp, +{silver or 0} sp", f"Postava: {char.name} (Hráč: {char.player.nickname}) -> Nový stav: {char.gold} gp, {char.silver} sp")
            elif action == 'minus':
                char.gold -= int(gold or 0)
                char.silver -= int(silver or 0)
                log_gold(f"-{gold or 0} gp, -{silver or 0} sp", f"Postava: {char.name} (Hráč: {char.player.nickname}) -> Nový stav: {char.gold} gp, {char.silver} sp")
            else:
                return redirect('dm_site_app:golds-management')

            char.save()

            # Zapsání do logu
            log = Logs(
                player=char.player,
                character=char,
                message=f"Přidáno: {gold} zlaťáků a {silver} stříbrňáků",
                value=plus_total_golds
            )
            log.save()

    return redirect('dm_site_app:golds-management')

@dm_required
def monster_gen_page(request):
    all_active_mobs = Monsters_Active.objects.all()
    all_monsters = Monsters_All_db.objects.all()
    

    context = {
        'active_mobs_list': all_active_mobs,
        'all_monsters': all_monsters,

    }
    return render(request, 'dm_site_app/monster_gen_page.html', context)

@dm_required
def random_monster_gen(request):
    if request.method == 'POST':
        mob_lvl = int(request.POST.get('mob_lvl')) # 1-30 (v databázi 0-29)
        mob_dificulty = int(request.POST.get('mob_dificulty')) # Obtížnost v rámci daného levelu

        final_dificulty = int(mob_dificulty - 3) # 1-2 = menší lvl než hráči, 3 = stejný lvl jak hráčí, 4-5 = větší lvl než hráčí
        final_lvl = float(mob_lvl + final_dificulty)
        final_lvl_min = max(0.0, final_lvl - 0.5)
        final_lvl_max = min(30.0, final_lvl + 0.5)

        # Vyhledá všechny monstra které mají CR v daném rozsahu
        monsters = Monsters_All_db.objects.filter(challenge_rating__gte=final_lvl_min, challenge_rating__lte=final_lvl_max)
        count = monsters.count()

        # Vybere náhodné monstrum
        if count > 0:
            random_mob = random.choice(monsters)
            active_mob = active_mob_db_save(random_mob.id)
            log_mob("Náhodný výběr monstra", f"CR {final_lvl_min}–{final_lvl_max} (nalezeno {count}x) -> Vybrán: {random_mob.name_cz or random_mob.name_en} (CR {random_mob.formatted_cr})")
            return redirect('dm_site_app:monster_gen_page') # Znova načte stránku s novým mobem
        else:
            log_warning("Náhodný výběr monstra", f"Žádné monstrum v databázi pro CR {final_lvl_min}–{final_lvl_max}")
            messages.error(request, "Nenalezeno na daný level")
            return redirect('dm_site_app:monster_gen_page')

@dm_required
def specific_monster_gen(request):
    if request.method == 'POST':
        monster_id = request.POST.get('monster_id')
        active_mob = active_mob_db_save(monster_id)
        if active_mob:
            log_mob("Výběr konkrétního monstra", f"Přidán: {active_mob.name_cz or active_mob.name_en} (CR {active_mob.formatted_cr})")
        return redirect('dm_site_app:monster_gen_page')
    else:
        log_warning("Výběr specifického monstra", "Neplatná metoda (očekáván POST)")
        messages.error(request, "Chyba při vybirani monstra")
        return redirect('dm_site_app:monster_gen_page')

@dm_required
def create_custom_monster(request):
    """
    Umožňuje DM vytvořit zcela novou nestvůru do herního bestiáře (Monsters_All_db)
    a volitelně ji rovnou nasadit do aktivních monster v probíhající hře (Monsters_Active).
    """
    sizes = ["Drobná", "Malá", "Střední", "Velká", "Obrovská", "Gigantická"]
    monster_types = [
        "Aberace", "Běs", "Drak", "Elementál", "Fey (Víla)", "Gigant",
        "Humanoid", "Konstrukt", "Monstrosita", "Nemrtvý", "Netvor",
        "Rostlina", "Sliz", "Zvíře", "Ostatní"
    ]
    alignments = [
        "Zákonné dobro", "Neutrální dobro", "Chaotické dobro",
        "Zákonný neutrál", "Čistý neutrál", "Chaotický neutrál",
        "Zákonné zlo", "Neutrální zlo", "Chaotické zlo",
        "Bez přesvědčení", "Jakékoliv přesvědčení"
    ]

    if request.method == 'POST':
        name_cz = request.POST.get('name_cz', '').strip()
        name_en = request.POST.get('name_en', '').strip() or name_cz

        if not name_cz:
            messages.error(request, "Vyplňte prosím český název monstra.")
            return render(request, 'dm_site_app/create_custom_monster.html', {
                'sizes': sizes,
                'monster_types': monster_types,
                'alignments': alignments,
                'current_page': 'monster_gen_page',
            })

        size = request.POST.get('size', 'Střední').strip() or 'Střední'
        monster_type = request.POST.get('monster_type', 'Monstrosita').strip() or 'Monstrosita'
        subtype = request.POST.get('subtype', '').strip()
        alignment = request.POST.get('alignment', 'Bez přesvědčení').strip() or 'Bez přesvědčení'

        # Bojové statistiky
        try:
            armor_class = max(1, int(request.POST.get('armor_class', 10) or 10))
        except (ValueError, TypeError):
            armor_class = 10

        armor_desc = request.POST.get('armor_desc', '').strip()

        try:
            hit_points = max(1, int(request.POST.get('hit_points', 15) or 15))
        except (ValueError, TypeError):
            hit_points = 15

        hit_dice = request.POST.get('hit_dice', '').strip()
        speed = request.POST.get('speed', '30 stop').strip() or '30 stop'

        # Vlastnosti
        def parse_ability(field, default=10):
            try:
                return max(1, min(30, int(request.POST.get(field, default) or default)))
            except (ValueError, TypeError):
                return default

        strength = parse_ability('strength', 10)
        dexterity = parse_ability('dexterity', 10)
        constitution = parse_ability('constitution', 10)
        intelligence = parse_ability('intelligence', 10)
        wisdom = parse_ability('wisdom', 10)
        charisma = parse_ability('charisma', 10)

        saving_throws = request.POST.get('saving_throws', '').strip()
        skills = request.POST.get('skills', '').strip()
        damage_vulnerabilities = request.POST.get('damage_vulnerabilities', '').strip()
        damage_resistances = request.POST.get('damage_resistances', '').strip()
        damage_immunities = request.POST.get('damage_immunities', '').strip()
        condition_immunities = request.POST.get('condition_immunities', '').strip()
        senses = request.POST.get('senses', 'pasivní Vnímání 10').strip()
        languages = request.POST.get('languages', '—').strip()

        try:
            challenge_rating = max(0.0, float(request.POST.get('challenge_rating', 1.0) or 1.0))
        except (ValueError, TypeError):
            challenge_rating = 1.0

        try:
            xp = max(0, int(request.POST.get('xp', 0) or 0))
        except (ValueError, TypeError):
            xp = 0

        try:
            proficiency_bonus = max(1, int(request.POST.get('proficiency_bonus', 2) or 2))
        except (ValueError, TypeError):
            proficiency_bonus = 2

        special_abilities = request.POST.get('special_abilities', '').strip()
        actions = request.POST.get('actions', '').strip()
        legendary_actions = request.POST.get('legendary_actions', '').strip()
        reactions = request.POST.get('reactions', '').strip()
        description = request.POST.get('description', '').strip()
        image_url = request.POST.get('image_url', '').strip()

        # Loot
        try:
            loot_gold = max(0, int(request.POST.get('loot_gold', 0) or 0))
        except (ValueError, TypeError):
            loot_gold = 0

        try:
            loot_silver = max(0, int(request.POST.get('loot_silver', 0) or 0))
        except (ValueError, TypeError):
            loot_silver = 0

        auto_activate = request.POST.get('auto_activate') in ('1', 'true', 'True', 'on')

        # Generování unikátního api_index
        slug = slugify(name_cz) or slugify(name_en) or 'custom-mob'
        api_index = f"custom-{slug[:35]}-{uuid.uuid4().hex[:6]}"

        new_compendium_mob = Monsters_All_db.objects.create(
            api_index=api_index,
            name_cz=name_cz,
            name_en=name_en,
            size=size,
            monster_type=monster_type,
            subtype=subtype,
            alignment=alignment,
            armor_class=armor_class,
            armor_desc=armor_desc,
            hit_points=hit_points,
            hit_dice=hit_dice,
            speed=speed,
            strength=strength,
            dexterity=dexterity,
            constitution=constitution,
            intelligence=intelligence,
            wisdom=wisdom,
            charisma=charisma,
            saving_throws=saving_throws,
            skills=skills,
            damage_vulnerabilities=damage_vulnerabilities,
            damage_resistances=damage_resistances,
            damage_immunities=damage_immunities,
            condition_immunities=condition_immunities,
            senses=senses,
            languages=languages,
            challenge_rating=challenge_rating,
            xp=xp,
            proficiency_bonus=proficiency_bonus,
            special_abilities=special_abilities,
            actions=actions,
            legendary_actions=legendary_actions,
            reactions=reactions,
            description=description,
            image_url=image_url,
            raw_data={},
            in_fight=False,
        )

        log_mob("Vytvořeno vlastní monstrum", f"{name_cz} (CR {new_compendium_mob.formatted_cr}) uloženo do kompendia")

        if auto_activate:
            new_active_mob = Monsters_Active.objects.create(
                api_index=api_index,
                name_cz=name_cz,
                name_en=name_en,
                size=size,
                monster_type=monster_type,
                subtype=subtype,
                alignment=alignment,
                armor_class=armor_class,
                armor_desc=armor_desc,
                hit_points=hit_points,
                current_hp=hit_points,
                hit_dice=hit_dice,
                speed=speed,
                strength=strength,
                dexterity=dexterity,
                constitution=constitution,
                intelligence=intelligence,
                wisdom=wisdom,
                charisma=charisma,
                saving_throws=saving_throws,
                skills=skills,
                damage_vulnerabilities=damage_vulnerabilities,
                damage_resistances=damage_resistances,
                damage_immunities=damage_immunities,
                condition_immunities=condition_immunities,
                senses=senses,
                languages=languages,
                challenge_rating=challenge_rating,
                xp=xp,
                proficiency_bonus=proficiency_bonus,
                special_abilities=special_abilities,
                actions=actions,
                legendary_actions=legendary_actions,
                reactions=reactions,
                description=description,
                image_url=image_url,
                raw_data={},
                in_fight=False,
                is_dead=False,
                loot_gold=loot_gold,
                loot_silver=loot_silver,
                loot_able=(loot_gold > 0 or loot_silver > 0),
            )
            messages.success(request, f"Monstrum '{name_cz}' (CR {new_compendium_mob.formatted_cr}) bylo úspěšně vytvořeno a ihned nasazeno do hry!")
        else:
            messages.success(request, f"Monstrum '{name_cz}' (CR {new_compendium_mob.formatted_cr}) bylo uloženo do bestiáře.")

        return redirect('dm_site_app:monster_gen_page')

    return render(request, 'dm_site_app/create_custom_monster.html', {
        'sizes': sizes,
        'monster_types': monster_types,
        'alignments': alignments,
        'current_page': 'monster_gen_page',
    })
        
@dm_required
def pvp_pre(request):
    all_active_mobs = Monsters_Active.objects.all()
    all_players = Char_info.objects.all()

    return render(request, 'dm_site_app/pvp_pre.html', {
        'current_page': 'pvp_pre',
        'all_active_mobs': all_active_mobs,
        'all_players': all_players,
    })


@dm_required
def pvp_arena(request):
    all_active_mobs = Monsters_Active.objects.filter(in_fight=True)
    all_players = Char_info.objects.filter(in_fight=True)
    log_arena("Načtena aréna", f"{all_active_mobs.count()} monster vs {all_players.count()} hráčů v boji")

    return render(request, 'dm_site_app/pvp_arena.html', {
        'current_page': 'pvp_arena',
        'all_active_mobs': all_active_mobs,
        'all_players': all_players,
    })

@dm_required
def api_update_hp(request):
    """
    API endpoint pro dávkový pozitivní update aktuálních životů (HP)
    pro monstra (Monsters_Active) i postavy hráčů (Char_info).
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Pouze metoda POST'}, status=405)

    try:
        data = json.loads(request.body)
        updates = data.get('updates')
        if updates is None:
            updates = [data]

        saved_records = []
        for item in updates:
            entity_type = item.get('entity_type')
            entity_id = item.get('entity_id')
            new_hp = int(item.get('current_hp'))

            if entity_type == 'mob':
                mob = Monsters_Active.objects.get(id=entity_id)
                old_hp = mob.current_hp
                mob.current_hp = new_hp
                mob.save(update_fields=['current_hp'])
                saved_records.append({'entity_type': 'mob', 'id': mob.id, 'current_hp': mob.current_hp})
                log_hp("Změna HP monstra", f"{mob.name_cz or mob.name_en}: {old_hp} -> {new_hp}/{mob.hit_points} HP")
            elif entity_type == 'player':
                player = Char_info.objects.get(id=entity_id)
                old_hp = player.hit_points_current
                player.hit_points_current = new_hp
                player.save(update_fields=['hit_points_current'])
                saved_records.append({'entity_type': 'player', 'id': player.id, 'current_hp': player.hit_points_current})
                log_hp("Změna HP hráče", f"{player.name}: {old_hp} -> {new_hp}/{player.hit_points_max} HP")

        return JsonResponse({'success': True, 'saved': saved_records})
    except Exception as e:
        log_error("Chyba při aktualizaci HP", str(e))
        return JsonResponse({'success': False, 'error': str(e)}, status=400)

@dm_required
def in_fight_switch(request):
    if request.method == 'POST':
        source_id = request.POST.get('source_id') # ID
        action = request.POST.get('in_fight') # True / False
        source = request.POST.get('source') # mob/ player

        if source == "mob":
            mob = get_object_or_404(Monsters_Active, id=source_id)
            mob.in_fight = (action == 'True') # Musí být takto, jinak to python vždycky zapíše jako "True"
            mob.save()
            action_desc = "VSTUPUJE DO BOJE ⚔️" if mob.in_fight else "ODCHÁZÍ Z BOJE 🏳️"
            log_arena(f"Monstrum: {action_desc}", f"{mob.name_cz or mob.name_en} [ID: {mob.id}]")
            return redirect('dm_site_app:pvp_pre')
        elif source == "player":
            player = Char_info.objects.get(id=source_id)
            player.in_fight = (action == 'True') # Musí být takto, jinak to python vždycky zapíše jako "True"
            player.save()
            action_desc = "VSTUPUJE DO BOJE ⚔️" if player.in_fight else "ODCHÁZÍ Z BOJE 🏳️"
            log_arena(f"Hráč: {action_desc}", f"{player.name} (Hráč: {player.player.nickname}) [ID: {player.id}]")
            return redirect('dm_site_app:pvp_pre')
    else:
        log_warning("Přepnutí stavu v boji", "Neplatná metoda požadavku (očekáván POST)")
        messages.error(request, "Chyba při vybirani monstra")
        return redirect('dm_site_app:pvp_pre') 

def active_mob_db_save(mob_id):
    mob = Monsters_All_db.objects.get(id=mob_id)

    if mob.monster_type == 'humanoid' or mob.monster_type == 'Humanoid':
        gold_base = 2
        silver_base = 6
        chance = 80
    elif mob.monster_type == 'undead' or mob.monster_type == 'Undead':
        gold_base = 2
        silver_base = 2
        chance = 10
    elif mob.monster_type == 'monstrosity' or mob.monster_type == 'Monstrosity':
        gold_base = 2
        silver_base = 2
        chance = 10
    else:
        gold_base = 0
        silver_base = 0
        chance = 0
        plus_gold = 0
        plus_silver = 0
        loot_able_switch = False

# spustí se jen pokud může mít mobka u sebe goldy
    print("--- GENERACE ZLATA U MONSTER --- ")
    print(f"Šance: {chance}%")
    print(f"Gold base: {gold_base}")
    print(f"Silver base: {silver_base}")
    if chance > 0:
        random_multi = int(round(mob.challenge_rating))
        if random_multi < 2:
            random_multi = 2
        random_bonus = random.uniform(1, random_multi)
        
        actual_gold = random.randint(1,gold_base)
        actual_silver = random.randint(1,silver_base)

        plus_gold = int(round(actual_gold * random_bonus))
        plus_silver = int(round(actual_silver * random_bonus))
        loot_able_switch = True

        while plus_silver >= 10:
            plus_gold += 1
            plus_silver -= 10

    # vytvoření nové mobky v aktivní databázi:
    new_mob = Monsters_Active.objects.create(
        api_index=mob.api_index,
        name_cz=mob.name_cz,
        name_en=mob.name_en,
        size=mob.size,
        monster_type=mob.monster_type,
        subtype=mob.subtype,
        alignment=mob.alignment,
        armor_class=mob.armor_class,
        armor_desc=mob.armor_desc,
        hit_points=mob.hit_points,
        current_hp=mob.hit_points,
        hit_dice=mob.hit_dice,
        speed=mob.speed,
        strength=mob.strength,
        dexterity=mob.dexterity,
        constitution=mob.constitution,
        intelligence=mob.intelligence,
        wisdom=mob.wisdom,
        charisma=mob.charisma,
        saving_throws=mob.saving_throws,
        skills=mob.skills,
        damage_vulnerabilities=mob.damage_vulnerabilities,
        damage_resistances=mob.damage_resistances,
        damage_immunities=mob.damage_immunities,
        condition_immunities=mob.condition_immunities,
        senses=mob.senses,
        languages=mob.languages,
        challenge_rating=mob.challenge_rating,
        xp=mob.xp,
        proficiency_bonus=mob.proficiency_bonus,
        special_abilities=mob.special_abilities,
        actions=mob.actions,
        legendary_actions=mob.legendary_actions,
        reactions=mob.reactions,
        description=mob.description,
        image_url=mob.image_url,
        raw_data=mob.raw_data,
        loot_gold=plus_gold,
        loot_silver=plus_silver,
        loot_able=loot_able_switch, 
    )
    log_success("Monstrum připraveno do hry", f"{new_mob.name_cz or new_mob.name_en} (CR {new_mob.formatted_cr}, {new_mob.hit_points} HP, AC {new_mob.armor_class}) [ID: {new_mob.id}]")
    return new_mob

@dm_required
def remove_mob(request, mob_id):
    mob = Monsters_Active.objects.filter(id=mob_id).first()
    if mob:
        name = mob.name_cz or mob.name_en
        mob.delete()
        log_mob("Monstrum odstraněno ze hry", f"{name} [ID: {mob_id}]")
    else:
        log_warning("Pokus o smazání neexistujícího monstra", f"ID: {mob_id}")
    return redirect('dm_site_app:monster_gen_page')

@dm_required
def mob_dead(request):

    if request.method == 'POST':
        mob_id = request.POST.get('mob_id')
        killer_id = request.POST.get('killer')

        mob = Monsters_Active.objects.filter(id=mob_id).first()
        killer = Char_info.objects.filter(id=killer_id).first()
        mob_name = (mob.name_cz or mob.name_en) if mob else f"ID {mob_id}"
        killer_name = killer.name if killer else f"ID {killer_id}"

        log_arena("Smrtící úder zaznamenán! 💀", f"Monstrum '{mob_name}' skoleno postavou '{killer_name}'")

# ACHIVEMENT
        smrtici_stroj_ach(char_id=killer_id, amount=1)
# LOOT
        #loot_gold(mob_id, killer_id) <--- Vypadá to, že není zájem
        #loot_items(mob_id, killer_id) <--- Vypadá to, že není zájem
        loot_temna_esence(mob_id, killer_id)
# LOG
        log = Logs(
            player=killer.player,
            character=killer,
            message=f"Postava {killer_name} porazila monstrum {mob_name}",
            value=None
        )
        log.save()

# ODEBRÁNÍ MONSTRA (MUSÍ BÝT NAKONEC!)

        mob.is_dead = True
        mob.in_fight = False
        mob.save()
        log_mob("Monstrum zabito", f"{mob_name} [ID: {mob_id}]")

        return redirect('dm_site_app:pvp_arena')
    return redirect('dm_site_app:pvp_arena')

@dm_required
def loot_management(request):

    all_chars = Char_info.objects.all().select_related('player')

    all_lootable_monsters = Monsters_Active.objects.filter(loot_able=True)
    alive_monsters = all_lootable_monsters.filter(is_dead=False)
    dead_monsters = all_lootable_monsters.filter(is_dead=True)

    all_lootable_npc = Npc.objects.filter(loot_able=True)
    alive_npc = all_lootable_npc.filter(is_dead=False)
    dead_npc = all_lootable_npc.filter(is_dead=True)

    all_items = Items_All_db.objects.all().order_by('name_cz')
    categories = sorted(list(set(Items_All_db.objects.values_list('category', flat=True).exclude(category__isnull=True).exclude(category=''))))

    context = {
        'all_chars': all_chars,
        'alive_monsters': alive_monsters,
        'dead_monsters': dead_monsters,
        'alive_npc': alive_npc,
        'dead_npc': dead_npc,
        'all_items': all_items,
        'categories': categories,
        'current_page': 'loot_management',
    }
    
    return render(request, 'dm_site_app/loot_management.html', context)


@dm_required
def plus_loot_gold(request):
    if request.method == 'POST':
        mob_id = int(request.POST.get('mob_id'))
        character_id = int(request.POST.get('character_id'))
        source = str(request.POST.get('source'))
    else:
        return redirect('dm_site_app:loot_management') 

# IDENTIFIKACE A PŘEPOČET
    if source == "mob":
        source_target = Monsters_Active.objects.filter(id=mob_id).first()
    elif source == "npc":
        source_target = Npc.objects.filter(id=mob_id).first()
    else:
        log_warning("Špatný source", f"Zadaný source {source} neexistuje")
        return redirect('dm_site_app:loot_management') 

    character = Char_info.objects.filter(id=character_id).first()
    plus_gold = int(source_target.loot_gold)
    plus_silver = int(source_target.loot_silver)
    plus_total_gold = float(plus_gold + (plus_silver / 10))

# PŘIPSÁNÍ POSTAVĚ
    character.gold += plus_gold
    character.silver += plus_silver
    character.total_golds += plus_total_gold
    character.save()

# ACHIVEMENT
    zbohatlik_ach(char_id=character_id, amount=plus_total_gold)

# Log
    log = Logs(
        player=character.player,
        character=character,
        message=f"Postava {character.name} získala {plus_gold} zlata a {plus_silver} stříbra",
        value=plus_total_gold,
    )
    log.save()
    log_gold(f"{character_id}, {plus_gold}, {plus_silver}")

# Odebrání
    source_target.loot_able = False
    source_target.save()

    return redirect('dm_site_app:loot_management')


@dm_required
def assign_loot_items(request):
    if request.method != 'POST':
        return redirect('dm_site_app:loot_management')

    character_id = request.POST.get('character_id')
    item_ids = request.POST.getlist('item_ids')
    if not item_ids and request.POST.get('item_ids_str'):
        item_ids = [i.strip() for i in request.POST.get('item_ids_str', '').split(',') if i.strip()]

    if not character_id or not item_ids:
        messages.warning(request, "Vyberte prosím postavu i alespoň jeden předmět.")
        return redirect('dm_site_app:loot_management')

    character = Char_info.objects.filter(id=character_id).first()
    if not character:
        messages.error(request, "Vybraná postava neexistuje.")
        return redirect('dm_site_app:loot_management')

    added_names = []
    for item_id in item_ids:
        try:
            item_id_int = int(item_id)
        except (ValueError, TypeError):
            continue

        item_template = Items_All_db.objects.filter(id=item_id_int).first()
        if item_template:
            active_item = Items_Active.objects.create(
                char_own=character,
                api_index=item_template.api_index,
                name_cz=item_template.name_cz,
                name_en=item_template.name_en,
                category=item_template.category,
                cost_gold=item_template.cost_gold,
                cost_silver=item_template.cost_silver,
                weight=item_template.weight,
                damage=item_template.damage,
                armor_class=item_template.armor_class,
                properties=item_template.properties,
                description=item_template.description,
            )
            added_names.append(active_item.name_cz or active_item.name_en or f"Předmět #{active_item.id}")

    if added_names:
        items_summary = ", ".join(added_names)
        messages.success(request, f"Postavě {character.name} bylo připsáno {len(added_names)} předmětů: {items_summary}")
        log = Logs(
            player=character.player,
            character=character,
            message=f"Postava {character.name} získala {len(added_names)} předmětů ({items_summary})",
            value=float(len(added_names))
        )
        log.save()
        log_success("Předměty připsány", f"Postava {character.name} získala: {items_summary}")
    else:
        messages.warning(request, "Nebyly nalezeny žádné platné předměty k připsání.")

    return redirect('dm_site_app:loot_management')


@dm_required
def create_custom_item(request):
    """
    Umožňuje DM vytvořit zcela nový předmět do herního kompendia (Items_All_db)
    a rovnou jej v zadaném množství připsat do inventáře vybrané postavy (Items_Active).
    """
    all_chars = Char_info.objects.all().select_related('player').order_by('name')
    categories = sorted(list(set(Items_All_db.objects.values_list('category', flat=True).exclude(category__isnull=True).exclude(category=''))))

    if request.method == 'POST':
        name_cz = request.POST.get('name_cz', '').strip()
        character_id = request.POST.get('character_id', '').strip()

        if not name_cz:
            messages.error(request, "Vyplňte prosím název předmětu.")
            return render(request, 'dm_site_app/create_custom_item.html', {
                'all_chars': all_chars,
                'categories': categories,
                'current_page': 'loot_management',
            })

        character = None
        if character_id:
            try:
                character = Char_info.objects.filter(id=int(character_id)).first()
            except (ValueError, TypeError):
                character = None

        # Množství (počet kusů)
        try:
            quantity = max(1, min(100, int(request.POST.get('quantity', 1) or 1)))
        except (ValueError, TypeError):
            quantity = 1

        # Kategorie
        category = request.POST.get('category', '').strip() or 'Ostatní'
        if category == '__custom__':
            custom_cat = request.POST.get('custom_category', '').strip()
            category = custom_cat if custom_cat else 'Ostatní'

        # Ceny a váha
        try:
            cost_gold = max(0, int(request.POST.get('cost_gold', 0) or 0))
        except (ValueError, TypeError):
            cost_gold = 0

        try:
            cost_silver = max(0, int(request.POST.get('cost_silver', 0) or 0))
        except (ValueError, TypeError):
            cost_silver = 0

        try:
            weight = max(0.0, float(request.POST.get('weight', 0.0) or 0.0))
        except (ValueError, TypeError):
            weight = 0.0

        description = request.POST.get('description', '').strip()
        name_en = request.POST.get('name_en', '').strip() or name_cz
        damage = request.POST.get('damage', '').strip() or None

        armor_class_raw = request.POST.get('armor_class', '').strip()
        armor_class = None
        if armor_class_raw:
            try:
                armor_class = int(armor_class_raw)
            except (ValueError, TypeError):
                armor_class = None

        properties = request.POST.get('properties', '').strip() or None

        # Generování unikátního api_index pro Items_All_db
        base_slug = slugify(name_cz)
        if not base_slug:
            base_slug = 'custom-item'
        api_index = f"custom-{base_slug[:60]}"
        if Items_All_db.objects.filter(api_index=api_index).exists():
            api_index = f"{api_index[:75]}-{uuid.uuid4().hex[:6]}"

        # 1. Uložení šablony předmětu do Items_All_db (Kompendium)
        item_template = Items_All_db.objects.create(
            api_index=api_index,
            name_cz=name_cz,
            name_en=name_en,
            category=category,
            cost_gold=cost_gold,
            cost_silver=cost_silver,
            weight=weight,
            damage=damage,
            armor_class=armor_class,
            properties=properties,
            description=description,
        )

        # 2. Vytvoření instancí v Items_Active pro vybraného hráče
        if character:
            for _ in range(quantity):
                Items_Active.objects.create(
                    char_own=character,
                    api_index=item_template.api_index,
                    name_cz=item_template.name_cz,
                    name_en=item_template.name_en,
                    category=item_template.category,
                    cost_gold=item_template.cost_gold,
                    cost_silver=item_template.cost_silver,
                    weight=item_template.weight,
                    damage=item_template.damage,
                    armor_class=item_template.armor_class,
                    properties=item_template.properties,
                    description=item_template.description,
                )

            log_msg = f"DM vytvořil a připsal předmět '{name_cz}' ({quantity}x) postavě {character.name}"
            log = Logs(
                player=character.player,
                character=character,
                message=log_msg,
                value=float(quantity)
            )
            log.save()
            log_success("Vlastní item vytvořen", log_msg)
            messages.success(request, f"Předmět '{name_cz}' ({quantity} ks) byl úspěšně vytvořen v databázi a připsán postavě {character.name}!")
        else:
            log_msg = f"DM vytvořil nový předmět '{name_cz}' do herního kompendia"
            log_info(log_msg)
            messages.success(request, f"Předmět '{name_cz}' byl úspěšně vytvořen v herním kompendiu!")

        return redirect('dm_site_app:loot_management')

    # GET požadavek
    selected_char_id = request.GET.get('char_id')
    context = {
        'all_chars': all_chars,
        'categories': categories,
        'selected_char_id': int(selected_char_id) if selected_char_id and selected_char_id.isdigit() else None,
        'current_page': 'loot_management',
    }
    return render(request, 'dm_site_app/create_custom_item.html', context)


# ==========================================
# 7. DM SPRÁVA INVENTÁŘŮ POSTAV (ODEBÍRÁNÍ PŘEDMĚTŮ)
# ==========================================

@dm_required
def player_inventory_management(request):
    """
    DM nástroj pro správu inventářů všech hráčských postav.
    Umožňuje DM prohlížet batoh jakéhokoliv hrdiny a mazat libovolné předměty (jednotlivě i hromadně).
    """
    all_chars = Char_info.objects.all().select_related('player').order_by('name')

    char_id = request.GET.get('char_id')
    selected_char = None
    if char_id:
        try:
            selected_char = all_chars.filter(id=int(char_id)).first()
        except (ValueError, TypeError):
            selected_char = None

    if not selected_char and all_chars.exists():
        selected_char = all_chars.first()

    items = []
    categories = []
    total_weight = 0.0
    if selected_char:
        items = Items_Active.objects.filter(char_own=selected_char).order_by('name_cz', 'name_en')
        categories = sorted(list(set(i.category for i in items if i.category)))
        total_weight = sum((i.weight or 0.0) for i in items)

    context = {
        'all_chars': all_chars,
        'selected_char': selected_char,
        'items': items,
        'categories': categories,
        'total_weight': round(total_weight, 2),
        'total_items_count': len(items),
        'current_page': 'tools',
    }
    return render(request, 'dm_site_app/player_inventory_management.html', context)


@dm_required
def dm_delete_player_item(request, item_id):
    """
    Umožňuje DM smazat jakýkoliv předmět z inventáře libovolné postavy.
    """
    if request.method != 'POST':
        messages.warning(request, "Smazání předmětu vyžaduje potvrzení formuláře.")
        return redirect('dm_site_app:player_inventory_management')

    item = get_object_or_404(Items_Active, id=item_id)
    char = item.char_own
    char_id = char.id if char else None
    item_name = item.name_cz or item.name_en or f"Předmět #{item.id}"
    char_name = char.name if char else "neznámá postava"

    item.delete()

    if char:
        Logs.objects.create(
            player=char.player,
            character=char,
            message=f"DM odebral předmět '{item_name}' postavě {char_name}",
            value=0.0
        )
    log_dm(f"DM smazal předmět '{item_name}' (ID: {item_id}) z inventáře postavy '{char_name}'")

    success_msg = f"Předmět '{item_name}' byl smazán z inventáře postavy {char_name}."
    messages.success(request, success_msg)

    if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.POST.get('ajax'):
        return JsonResponse({
            'status': 'ok',
            'deleted_id': item_id,
            'item_name': item_name,
            'message': success_msg
        })

    redirect_url = reverse('dm_site_app:player_inventory_management')
    if char_id:
        redirect_url += f'?char_id={char_id}'
    return redirect(redirect_url)


@dm_required
def dm_bulk_delete_player_items(request):
    """
    Umožňuje DM hromadně smazat vybrané předměty z inventáře postavy.
    """
    if request.method != 'POST':
        return redirect('dm_site_app:player_inventory_management')

    char_id = request.POST.get('character_id')
    item_ids = request.POST.getlist('item_ids')
    if not item_ids and request.POST.get('item_ids_str'):
        item_ids = [i.strip() for i in request.POST.get('item_ids_str', '').split(',') if i.strip()]

    if not item_ids:
        messages.warning(request, "Nebyly vybrány žádné předměty ke smazání.")
        redirect_url = reverse('dm_site_app:player_inventory_management')
        if char_id:
            redirect_url += f'?char_id={char_id}'
        return redirect(redirect_url)

    character = None
    if char_id:
        character = Char_info.objects.filter(id=char_id).first()

    deleted_names = []
    qs = Items_Active.objects.filter(id__in=item_ids)
    if character:
        qs = qs.filter(char_own=character)

    for item in qs:
        name = item.name_cz or item.name_en or f"Předmět #{item.id}"
        deleted_names.append(name)
        item.delete()

    if deleted_names:
        summary = ", ".join(deleted_names)
        char_name = character.name if character else "vybrané postavy"
        if character:
            Logs.objects.create(
                player=character.player,
                character=character,
                message=f"DM hromadně odebral {len(deleted_names)} předmětů ({summary}) postavě {char_name}",
                value=float(len(deleted_names))
            )
        log_dm(f"DM hromadně smazal {len(deleted_names)} předmětů postavě {char_name}: {summary}")
        messages.success(request, f"Úspěšně smazáno {len(deleted_names)} předmětů z inventáře postavy {char_name}: {summary}")
    else:
        messages.warning(request, "Nebyly nalezeny žádné odpovídající předměty ke smazání.")

    redirect_url = reverse('dm_site_app:player_inventory_management')
    if char_id:
        redirect_url += f'?char_id={char_id}'
    return redirect(redirect_url)


# ==========================================
# 7. SPRÁVA ÚSPĚCHŮ (ACHIEVEMENTS MANAGEMENT)
# ==========================================

@dm_required
def achievements_management(request):
    """
    Správa herních úspěchů (Achievements) v DM sekci.
    Umožňuje:
    - Prohlížet a filtrovat přiřazené úspěchy hráčů a postav
    - Přiřadit jakýkoliv úspěch jakékoliv postavě s vlastní počáteční hodnotou
    - Upravovat hodnoty získaných úspěchů
    - Mazat záznamy úspěchů
    - Spravovat šablony úspěchů (vytvářet nové, editovat milníky a ikony)
    """
    char_id = request.GET.get('char_id')
    player_id = request.GET.get('player_id')
    query = request.GET.get('q', '').strip()
    active_tab = request.GET.get('tab', 'players')

    all_characters = Char_info.objects.select_related('player', 'player__user').order_by('name')
    all_players = Player.objects.select_related('user').order_by('nickname', 'user__username')
    all_templates = Achivements_database.objects.all().order_by('name')

    selected_char = None
    if char_id:
        selected_char = Char_info.objects.filter(id=char_id).select_related('player').first()

    selected_player = None
    if player_id:
        selected_player = Player.objects.filter(id=player_id).first()

    player_achievements_qs = Achivements_players.objects.select_related(
        'player', 'player__user', 'char', 'Achivement'
    ).order_by('-current_value')

    if selected_char:
        player_achievements_qs = player_achievements_qs.filter(char=selected_char)
    elif selected_player:
        player_achievements_qs = player_achievements_qs.filter(player=selected_player)

    if query:
        player_achievements_qs = player_achievements_qs.filter(
            Q(char__name__icontains=query) |
            Q(player__nickname__icontains=query) |
            Q(player__user__username__icontains=query) |
            Q(Achivement__name__icontains=query) |
            Q(Achivement__description__icontains=query)
        )

    return render(request, 'dm_site_app/achievements_management.html', {
        'current_page': 'achievements_management',
        'active_tab': active_tab,
        'all_characters': all_characters,
        'all_players': all_players,
        'all_templates': all_templates,
        'selected_char': selected_char,
        'selected_player': selected_player,
        'player_achievements': player_achievements_qs,
        'query': query,
    })


@dm_required
def dm_assign_achievement(request):
    """Přiřadí vybraný úspěch postavě nebo upraví jeho hodnotu."""
    if request.method != 'POST':
        return redirect('dm_site_app:achievements_management')

    char_id = request.POST.get('character_id')
    template_id = request.POST.get('template_id')
    raw_value = (request.POST.get('current_value') or '0').replace(',', '.').strip()
    action_mode = request.POST.get('mode', 'set')

    try:
        current_val = float(raw_value)
    except (ValueError, TypeError):
        current_val = 0.0

    character = get_object_or_404(Char_info, id=char_id)
    template = get_object_or_404(Achivements_database, id=template_id)
    player = character.player

    existing = Achivements_players.objects.filter(char=character, Achivement=template).first()
    if existing:
        old_val = existing.current_value
        if action_mode == 'add':
            existing.current_value += current_val
        else:
            existing.current_value = current_val
        existing.save()
        log_msg = f"DM upravil úspěch '{template.name}' postavě {character.name}: {old_val} -> {existing.current_value} (úroveň: {existing.get_current_status_display() or 'Nesplněno'})"
        messages.success(request, f"Úspěch „{template.name}“ postavy {character.name} byl upraven na hodnotu {existing.current_value}.")
    else:
        existing = Achivements_players.objects.create(
            player=player,
            char=character,
            Achivement=template,
            current_value=current_val
        )
        existing.save()
        log_msg = f"DM přiřadil nový úspěch '{template.name}' postavě {character.name} s hodnotou {current_val} (úroveň: {existing.get_current_status_display() or 'Nesplněno'})"
        messages.success(request, f"Úspěch „{template.name}“ byl úspěšně přiřazen postavě {character.name} s hodnotou {current_val}.")

    if player:
        Logs.objects.create(
            player=player,
            character=character,
            message=log_msg,
            value=existing.current_value
        )
    log_dm(log_msg)

    redirect_url = reverse('dm_site_app:achievements_management')
    if char_id:
        redirect_url += f"?char_id={char_id}"
    return redirect(redirect_url)


@dm_required
def dm_update_achievement_value(request, ach_player_id):
    """Rychlá úprava hodnoty již získaného úspěchu postavy."""
    if request.method != 'POST':
        return redirect('dm_site_app:achievements_management')

    ach_player = get_object_or_404(Achivements_players, id=ach_player_id)
    raw_value = (request.POST.get('current_value') or '').replace(',', '.').strip()
    delta_str = (request.POST.get('delta') or '').replace(',', '.').strip()

    old_val = ach_player.current_value
    if delta_str:
        try:
            delta = float(delta_str)
            ach_player.current_value += delta
        except (ValueError, TypeError):
            pass
    elif raw_value != '':
        try:
            ach_player.current_value = float(raw_value)
        except (ValueError, TypeError):
            pass

    ach_player.save()
    char_name = ach_player.char.name if ach_player.char else "Neznámá"
    ach_name = ach_player.Achivement.name if ach_player.Achivement else "Neznámý"

    log_msg = f"DM změnil hodnotu úspěchu '{ach_name}' postavy {char_name}: {old_val} -> {ach_player.current_value} (status: {ach_player.get_current_status_display() or 'Nesplněno'})"
    if ach_player.player and ach_player.char:
        Logs.objects.create(
            player=ach_player.player,
            character=ach_player.char,
            message=log_msg,
            value=ach_player.current_value
        )
    log_dm(log_msg)

    if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.POST.get('ajax'):
        return JsonResponse({
            'status': 'ok',
            'id': ach_player.id,
            'current_value': ach_player.current_value,
            'current_status': ach_player.current_status,
            'current_status_display': ach_player.get_current_status_display() or 'Nesplněno',
            'message': f"Hodnota úspěchu byla změněna na {ach_player.current_value}."
        })

    messages.success(request, f"Hodnota úspěchu „{ach_name}“ byla úspěšně změněna na {ach_player.current_value}.")
    char_id = ach_player.char_id
    redirect_url = reverse('dm_site_app:achievements_management')
    if char_id:
        redirect_url += f"?char_id={char_id}"
    return redirect(redirect_url)


@dm_required
def dm_delete_player_achievement(request, ach_player_id):
    """Smaže záznam úspěchu dané postavy."""
    if request.method != 'POST':
        return redirect('dm_site_app:achievements_management')

    ach_player = get_object_or_404(Achivements_players, id=ach_player_id)
    char_id = ach_player.char_id
    char_name = ach_player.char.name if ach_player.char else "Neznámá"
    ach_name = ach_player.Achivement.name if ach_player.Achivement else "Neznámý"

    log_msg = f"DM smazal úspěch '{ach_name}' z profilu postavy {char_name}."
    if ach_player.player and ach_player.char:
        Logs.objects.create(
            player=ach_player.player,
            character=ach_player.char,
            message=log_msg,
            value=ach_player.current_value
        )
    ach_player.delete()
    log_dm(log_msg)

    messages.success(request, f"Úspěch „{ach_name}“ byl odebrán postavě {char_name}.")
    redirect_url = reverse('dm_site_app:achievements_management')
    if char_id:
        redirect_url += f"?char_id={char_id}"
    return redirect(redirect_url)


@dm_required
def dm_create_achievement_template(request):
    """Vytvoří novou šablonu úspěchu v Achivements_database."""
    if request.method != 'POST':
        return redirect('dm_site_app:achievements_management')

    name = request.POST.get('name', '').strip()
    description = request.POST.get('description', '').strip()
    if not name:
        messages.error(request, "Název úspěchu je povinný!")
        return redirect(reverse('dm_site_app:achievements_management') + "?tab=templates")

    def parse_float(key, default=1.0):
        val = (request.POST.get(key) or '').replace(',', '.').strip()
        try:
            return float(val) if val else default
        except ValueError:
            return default

    new_template = Achivements_database(
        name=name,
        description=description,
        bronze_value=parse_float('bronze_value', 1.0),
        silver_value=parse_float('silver_value', 1.0),
        gold_value=parse_float('gold_value', 1.0),
        platinum_value=parse_float('platinum_value', 1.0),
        emerald_value=parse_float('emerald_value', 1.0),
        diamond_value=parse_float('diamond_value', 1.0),
    )
    if 'image' in request.FILES:
        new_template.image = request.FILES['image']
    new_template.save()

    log_dm(f"DM vytvořil novou šablonu úspěchu '{name}' (ID: {new_template.id})")
    messages.success(request, f"Nová šablona úspěchu „{name}“ byla úspěšně vytvořena!")
    return redirect(reverse('dm_site_app:achievements_management') + "?tab=templates")


@dm_required
def dm_edit_achievement_template(request, template_id):
    """Upraví existující šablonu úspěchu."""
    if request.method != 'POST':
        return redirect('dm_site_app:achievements_management')

    template = get_object_or_404(Achivements_database, id=template_id)
    name = request.POST.get('name', '').strip()
    description = request.POST.get('description', '').strip()

    if not name:
        messages.error(request, "Název úspěchu nesmí být prázdný!")
        return redirect(reverse('dm_site_app:achievements_management') + "?tab=templates")

    def parse_float(key, default):
        val = (request.POST.get(key) or '').replace(',', '.').strip()
        try:
            return float(val) if val else default
        except ValueError:
            return default

    template.name = name
    template.description = description
    template.bronze_value = parse_float('bronze_value', template.bronze_value or 1.0)
    template.silver_value = parse_float('silver_value', template.silver_value or 1.0)
    template.gold_value = parse_float('gold_value', template.gold_value or 1.0)
    template.platinum_value = parse_float('platinum_value', template.platinum_value or 1.0)
    template.emerald_value = parse_float('emerald_value', template.emerald_value or 1.0)
    template.diamond_value = parse_float('diamond_value', template.diamond_value or 1.0)

    if 'image' in request.FILES:
        template.image = request.FILES['image']
    template.save()

    # Přepočet všech existujících hráčských instancí tohoto úspěchu
    for p_ach in template.achivements.all():
        p_ach.save()

    log_dm(f"DM upravil šablonu úspěchu '{name}' (ID: {template.id})")
    messages.success(request, f"Šablona úspěchu „{name}“ byla úspěšně aktualizována!")
    return redirect(reverse('dm_site_app:achievements_management') + "?tab=templates")


# ==========================================
# 8. SPRÁVA POZIC PRO KOUZLA (SPELL SLOTS)
# ==========================================

@dm_required
def spell_slots_management(request):
    """8. Správa volných pozic pro kouzla (Spell Sloty) jednotlivých postav."""
    all_chars = Char_info.objects.select_related('player', 'player__user').prefetch_related('spell_slots').order_by('name')
    context = {
        'all_chars': all_chars,
        'current_page': 'spell_slots_management',
    }
    return render(request, 'dm_site_app/spell_slots_management.html', context)


@dm_required
def modify_spell_slots(request):
    """
    Rychlé přidávání a odebírání volných pozic pro kouzla nebo nastavení maximálních pozic.
    Podporuje akce:
    - plus: přidá 1 volnou pozici pro daný level
    - minus: ubere 1 volnou pozici pro daný level
    - restore_all: obnoví všechny volné pozice na maximum (dlouhý odpočinek)
    - set_slot: vytvoří nebo upraví úroveň slotu (max_slots, current_slots)
    - delete_slot: smaže daný slot
    """
    if request.method != 'POST':
        return redirect('dm_site_app:spell_slots_management')

    is_ajax = (
        request.headers.get('x-requested-with') == 'XMLHttpRequest' or
        'application/json' in request.headers.get('Accept', '') or
        request.POST.get('ajax') == '1'
    )

    action = request.POST.get('action')
    char_id = request.POST.get('char_id') or request.POST.get('character_id')
    slot_id = request.POST.get('slot_id')

    if not char_id and not slot_id:
        if is_ajax:
            return JsonResponse({'success': False, 'status': 'error', 'error': 'Chybí identifikátor postavy nebo slotu.'}, status=400)
        messages.error(request, "Chybí identifikátor postavy nebo slotu.")
        return redirect('dm_site_app:spell_slots_management')

    if slot_id:
        slot = get_object_or_404(CharacterSpellSlot, id=slot_id)
        char = slot.character
    else:
        char = get_object_or_404(Char_info, id=char_id)
        slot = None

    if action == 'plus':
        if not slot:
            try:
                level = int(request.POST.get('level', 1))
            except (ValueError, TypeError):
                level = 1
            slot, _ = CharacterSpellSlot.objects.get_or_create(character=char, level=level, defaults={'current_slots': 0, 'max_slots': 0})

        if slot.max_slots > 0:
            slot.current_slots = min(slot.max_slots, slot.current_slots + 1)
        else:
            slot.current_slots += 1
        slot.save()
        log_dm(f"DM přidal volnou pozici pro kouzlo ({slot.level}. úroveň) postavě {char.name}: {slot.current_slots}/{slot.max_slots}")

        if is_ajax:
            return JsonResponse({
                'success': True,
                'status': 'ok',
                'char_id': char.id,
                'slot_id': slot.id,
                'level': slot.level,
                'current_slots': slot.current_slots,
                'max_slots': slot.max_slots,
            })
        messages.success(request, f"Přidána 1 volná pozice {slot.level}. úrovně pro postavu {char.name} ({slot.current_slots}/{slot.max_slots}).")

    elif action == 'minus':
        if not slot:
            try:
                level = int(request.POST.get('level', 1))
            except (ValueError, TypeError):
                level = 1
            slot, _ = CharacterSpellSlot.objects.get_or_create(character=char, level=level, defaults={'current_slots': 0, 'max_slots': 0})

        slot.current_slots = max(0, slot.current_slots - 1)
        slot.save()
        log_dm(f"DM odebral volnou pozici pro kouzlo ({slot.level}. úroveň) postavě {char.name}: {slot.current_slots}/{slot.max_slots}")

        if is_ajax:
            return JsonResponse({
                'success': True,
                'status': 'ok',
                'char_id': char.id,
                'slot_id': slot.id,
                'level': slot.level,
                'current_slots': slot.current_slots,
                'max_slots': slot.max_slots,
            })
        messages.success(request, f"Odebrána 1 volná pozice {slot.level}. úrovně pro postavu {char.name} ({slot.current_slots}/{slot.max_slots}).")

    elif action == 'restore_all':
        for s in char.spell_slots.all():
            s.current_slots = s.max_slots
            s.save()
        log_dm(f"DM obnovil všechny pozice pro kouzla postavě {char.name} na maximum (Dlouhý odpočinek).")
        if is_ajax:
            slots_data = [{
                'id': s.id,
                'level': s.level,
                'current_slots': s.current_slots,
                'max_slots': s.max_slots
            } for s in char.spell_slots.all()]
            return JsonResponse({'success': True, 'status': 'ok', 'char_id': char.id, 'slots': slots_data})
        messages.success(request, f"Všechny pozice pro kouzla postavy {char.name} byly plně obnoveny na maximum.")

    elif action == 'set_slot':
        try:
            level = max(1, min(9, int(request.POST.get('level', 1))))
            max_slots = max(0, int(request.POST.get('max_slots', 0)))
            raw_curr = request.POST.get('current_slots')
            if raw_curr is not None and raw_curr != '':
                current_slots = max(0, int(raw_curr))
            else:
                current_slots = max_slots
        except (ValueError, TypeError):
            if is_ajax:
                return JsonResponse({'success': False, 'status': 'error', 'error': 'Neplatné číselné hodnoty.'}, status=400)
            messages.error(request, "Zadejte platné číselné hodnoty pro úroveň a počet slotů.")
            return redirect('dm_site_app:spell_slots_management')

        slot, created = CharacterSpellSlot.objects.get_or_create(
            character=char,
            level=level,
            defaults={'max_slots': max_slots, 'current_slots': current_slots}
        )
        if not created:
            slot.max_slots = max_slots
            slot.current_slots = min(max_slots, current_slots) if max_slots > 0 else current_slots
            slot.save()

        log_dm(f"DM nastavil pozice pro kouzla {level}. úrovně postavě {char.name}: {slot.current_slots}/{slot.max_slots}")
        if is_ajax:
            return JsonResponse({
                'success': True,
                'status': 'ok',
                'char_id': char.id,
                'slot_id': slot.id,
                'level': slot.level,
                'current_slots': slot.current_slots,
                'max_slots': slot.max_slots,
            })
        messages.success(request, f"Pozice pro kouzla {level}. úrovně pro postavu {char.name} byly nastaveny na {slot.current_slots} / {slot.max_slots}.")

    elif action == 'delete_slot':
        if slot:
            lvl = slot.level
            slot.delete()
            log_dm(f"DM smazal sloty {lvl}. úrovně postavy {char.name}.")
            if is_ajax:
                return JsonResponse({'success': True, 'status': 'ok', 'char_id': char.id, 'deleted_level': lvl})
            messages.success(request, f"Sloty {lvl}. úrovně pro postavu {char.name} byly smazány.")

    return redirect('dm_site_app:spell_slots_management')



