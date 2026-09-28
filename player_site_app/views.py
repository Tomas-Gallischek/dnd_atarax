from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Player, Char_info
from .forms import PlayerLoginForm, PlayerRegistrationForm


def index(request):
    """
    Úvodní stránka hráčské sekce:
    Pokud je hráč přihlášen, přesměruje ho na přehled postav.
    Pokud není přihlášen, nabídne přihlášení a registraci.
    """
    if request.user.is_authenticated:
        return redirect('player_site_app:prehled_postav')

    login_form = PlayerLoginForm()
    reg_form = PlayerRegistrationForm()

    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'register':
            reg_form = PlayerRegistrationForm(request.POST)
            if reg_form.is_valid():
                user = reg_form.save()
                login(request, user)
                messages.success(request, f"Registrace proběhla úspěšně! Vítej, {user.player.nickname or user.username}.")
                return redirect('player_site_app:prehled_postav')
            else:
                messages.error(request, "Opravte prosím chyby v registračním formuláři.")
        
        elif action == 'login':
            login_form = PlayerLoginForm(request, data=request.POST)
            if login_form.is_valid():
                user = login_form.get_user()
                login(request, user)
                # Ujistíme se, že k uživateli existuje profil Player
                Player.objects.get_or_create(user=user, defaults={'nickname': user.username})
                messages.success(request, f"Přihlášení proběhlo úspěšně. Vítej zpět!")
                next_url = request.GET.get('next')
                if next_url:
                    return redirect(next_url)
                return redirect('player_site_app:prehled_postav')
            else:
                messages.error(request, "Neplatné uživatelské jméno nebo heslo.")

    return render(request, 'player_site_app/login_index.html', {
        'login_form': login_form,
        'reg_form': reg_form,
    })


def logout_view(request):
    """Odhlásí hráče a přesměruje na login."""
    logout(request)
    messages.info(request, "Byl jsi úspěšně odhlášen.")
    return redirect('player_site_app:index')


@login_required(login_url='player_site_app:index')
def prehled_postav(request):
    """Zobrazí seznam postav patřících POUZE aktuálně přihlášenému hráči."""
    player, _ = Player.objects.get_or_create(user=request.user, defaults={'nickname': request.user.username})
    characters = player.characters.all()
    
    return render(request, 'player_site_app/prehled_postav.html', {
        'player': player,
        'characters': characters,
    })


@login_required(login_url='player_site_app:index')
def char_overview(request, char_id):
    """
    Zobrazí detailní přehled konkrétní postavy.
    Přístup je povolen POUZE pokud postava patří přihlášenému hráči.
    """
    character = get_object_or_404(Char_info, id=char_id, player__user=request.user)
    
    return render(request, 'player_site_app/char_over_view..html', {
        'character': character,
        'player': character.player,
    })
