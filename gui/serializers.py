from . import models, tasks
import io
from PIL import Image
from rest_framework import serializers
import secrets
from django.conf import settings
from bitcart.coins.btc import BTC

RPC_USER = settings.RPC_USER
RPC_PASS = settings.RPC_PASS

RPC_URL = settings.RPC_URL


def edit_image(validated_data):
    # TODO: remove
    image_field = validated_data.get('image')
    if image_field:
        image_file = io.BytesIO(image_field.read())
        image = Image.open(image_file)
        w, h = image.size

        image = image.resize((416, 416), Image.ANTIALIAS)

        image_file = io.BytesIO()
        image.save(image_file, 'JPEG', quality=90)

        image_field.file = image_file
    return validated_data


class WalletSerializer(serializers.ModelSerializer):
    balance = serializers.SerializerMethodField()

    class Meta:
        model = models.Wallet
        fields = ("id", "name", "xpub", "user", "balance")

    def get_balance(self, obj):
        return BTC(RPC_URL, xpub=obj.xpub, rpc_user=RPC_USER,
                   rpc_pass=RPC_PASS).balance()['confirmed']


class StoreSerializer(serializers.ModelSerializer):
    wallet_name = serializers.ReadOnlyField(source="wallet.name")

    class Meta:
        model = models.Store
        fields = ("id", "name", "domain", "template",
                  "email", "wallet_name", "wallet")


class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Product
        fields = "__all__"
        datatables_always_serialize = ('status')

    def create(self, validated_data):
        validated_data = edit_image(validated_data)
        return super().create(validated_data)

    def update(self, instance, validated_data):
        for i in validated_data:
            instance.__dict__[i] = validated_data[i]
        validated_data = edit_image(validated_data)
        instance.image = validated_data.get("image")
        instance.save()
        return instance


class InvoiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Invoice
        fields = "__all__"
        datatables_always_serialize = ('status')

    def create(self, validated_data):
        data_got = BTC(RPC_URL, xpub=validated_data["products"][0].store.wallet.xpub, rpc_user=RPC_USER, rpc_pass=RPC_PASS).addrequest(
            validated_data["amount"], description=validated_data["products"][0].description)
        validated_data["bitcoin_address"] = data_got["address"]
        validated_data["bitcoin_url"] = data_got["URI"]
        validated_data = edit_image(validated_data)
        return super().create(validated_data)

    def update(self, instance, validated_data):
        for i in validated_data:
            instance.__dict__[i] = validated_data[i]
        validated_data = edit_image(validated_data)
        instance.image = validated_data.get("image")
        instance.save()
        return instance
