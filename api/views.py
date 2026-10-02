from api import models
from api.permissions import IsOwnerOrReadOnly
from rest_framework import generics, permissions, filters, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView
from .serializers import RegisterSerializer, HabitCreateUpdateSerializer, HabitListRetrieveSerializer
from .models import CustomUser, Habit
from rest_framework.authtoken.models import Token
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend


class RegisterView(generics.CreateAPIView):
    queryset = CustomUser.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]


class LoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        from django.contrib.auth import authenticate

        email = request.data.get("email")
        password = request.data.get("password")

        user = authenticate(request, email=email, password=password)

        if user is not None:
            token, created = Token.objects.get_or_create(user=user)
            return Response({"token": token.key})
        else:
            return Response({"error": "Неверные учетные данные"}, status=400)


class HabitViewSet(viewsets.ModelViewSet):
    queryset = Habit.objects.all()

    # Используем разные сериализаторы для чтения и записи
    def get_serializer_class(self):
        if self.action in ["list", "retrieve"]:
            return HabitListRetrieveSerializer
        return HabitCreateUpdateSerializer

    permission_classes = [IsAuthenticated, IsOwnerOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["is_public", "is_pleasant"]
    search_fields = ["action", "place"]  # Поиск по действию и месту
    ordering_fields = ["time", "created_at"]  # Если добавите created_at в модель

    def perform_create(self, serializer):
        # При создании привычки автоматически проставляем владельца
        serializer.save(owner=self.request.user)

    def get_queryset(self):
        # Пользователь видит свои ЛЮБЫЕ привычки + публичные привычки других
        user = self.request.user
        if user.is_authenticated:
            return Habit.objects.filter(models.Q(owner=user) | models.Q(is_public=True)).distinct()
        # Анонимные пользователи видят только публичные
        return Habit.objects.filter(is_public=True)


class SetTelegramIdView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """Пользователь отправляет свой chat_id из диалога с  Телеграм-ботом,сохраняем его в профиль."""
        chat_id = request.data.get("chat_id")
        if not chat_id or not isinstance(chat_id, int):
            return Response({"error": "Invalid chat_id"}, status=400)

        request.user.telegram_chat_id = chat_id
        request.user.save()

        return Response({"status": "ok"})
