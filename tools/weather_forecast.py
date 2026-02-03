"""日本の天気予報を取得するツール

気象庁のAPIを使用して、都道府県別の天気予報を取得します。
"""

import json
from typing import Literal
import urllib.request
import urllib.error

from strands import tool


# テロップコードと天気の対応表（主要なもの）
TELOP_CODES = {
    100: "晴れ",
    101: "晴れ時々くもり",
    102: "晴れ一時雨",
    103: "晴れ時々雨",
    104: "晴れ一時雪",
    110: "晴れのち時々くもり",
    111: "晴れのちくもり",
    112: "晴れのち一時雨",
    113: "晴れのち時々雨",
    114: "晴れのち雨",
    115: "晴れのち一時雪",
    116: "晴れのち雪",
    200: "くもり",
    201: "くもり時々晴れ",
    202: "くもり一時雨",
    203: "くもり時々雨",
    204: "くもり一時雪",
    210: "くもりのち時々晴れ",
    211: "くもりのち晴れ",
    212: "くもりのち一時雨",
    213: "くもりのち時々雨",
    214: "くもりのち雨",
    215: "くもりのち一時雪",
    216: "くもりのち雪",
    300: "雨",
    301: "雨時々晴れ",
    302: "雨時々止む",
    303: "雨時々雪",
    304: "雨か雪",
    311: "雨のち晴れ",
    313: "雨のちくもり",
    314: "雨のち時々雪",
    315: "雨のち雪",
    400: "雪",
    401: "雪時々晴れ",
    402: "雪時々止む",
    403: "雪時々雨",
    411: "雪のち晴れ",
    413: "雪のちくもり",
    414: "雪のち雨",
}


def _fetch_json(url: str) -> dict:
    """URLからJSONデータを取得する"""
    try:
        with urllib.request.urlopen(url) as response:
            return json.loads(response.read().decode('utf-8'))
    except urllib.error.URLError as e:
        raise Exception(f"データの取得に失敗しました: {e}")


def _find_prefecture_code(prefecture_name: str) -> str:
    """都道府県名から地域コードを取得する"""
    area_data = _fetch_json("https://www.jma.go.jp/bosai/common/const/area.json")

    # offices（都道府県レベル）から検索
    offices = area_data.get("offices", {})

    for code, info in offices.items():
        name = info.get("name", "")
        # 都道府県名の部分一致で検索
        if prefecture_name in name or name in prefecture_name:
            return code

    # 見つからない場合はエラー
    raise ValueError(f"都道府県名 '{prefecture_name}' に該当する地域が見つかりませんでした")


def _decode_telop(weather_code: int) -> str:
    """テロップコードを日本語の天気説明に変換する"""
    return TELOP_CODES.get(weather_code, f"不明な天気コード: {weather_code}")


def _format_forecast_data(forecast_data: list, forecast_type: str) -> dict:
    """予報データを整形する"""
    result = {
        "forecast_type": forecast_type,
        "areas": []
    }

    for area_forecast in forecast_data:
        publishing_office = area_forecast.get("publishingOffice", "")
        report_datetime = area_forecast.get("reportDatetime", "")

        # 地域ごとの予報を処理
        time_series = area_forecast.get("timeSeries", [])

        for series in time_series:
            time_defines = series.get("timeDefines", [])
            areas = series.get("areas", [])

            for area in areas:
                area_name = area.get("area", {}).get("name", "")
                area_code = area.get("area", {}).get("code", "")

                area_info = {
                    "area_name": area_name,
                    "area_code": area_code,
                    "publishing_office": publishing_office,
                    "report_datetime": report_datetime,
                    "forecasts": []
                }

                # 天気予報の詳細
                weathers = area.get("weathers", [])
                weather_codes = area.get("weatherCodes", [])
                winds = area.get("winds", [])
                waves = area.get("waves", [])
                pops = area.get("pops", [])  # 降水確率
                temps = area.get("temps", [])  # 気温
                temps_min = area.get("tempsMin", [])  # 最低気温
                temps_max = area.get("tempsMax", [])  # 最高気温

                for i, time_define in enumerate(time_defines):
                    forecast_item = {
                        "datetime": time_define
                    }

                    if i < len(weathers):
                        forecast_item["weather"] = weathers[i]

                    if i < len(weather_codes):
                        code = int(weather_codes[i]) if weather_codes[i] else 0
                        forecast_item["weather_code"] = code
                        forecast_item["weather_description"] = _decode_telop(code)

                    if i < len(winds):
                        forecast_item["wind"] = winds[i]

                    if i < len(waves):
                        forecast_item["wave"] = waves[i]

                    if i < len(pops):
                        forecast_item["precipitation_probability"] = pops[i]

                    if i < len(temps):
                        forecast_item["temperature"] = temps[i]

                    if i < len(temps_min):
                        forecast_item["temperature_min"] = temps_min[i]

                    if i < len(temps_max):
                        forecast_item["temperature_max"] = temps_max[i]

                    area_info["forecasts"].append(forecast_item)

                result["areas"].append(area_info)

    return result


@tool
def get_weather_forecast(
    prefecture_name: str,
    forecast_type: Literal["short", "weekly"] = "short"
) -> str:
    """日本の都道府県別天気予報を取得します。

    気象庁のAPIを使用して、指定された都道府県の天気予報を取得します。
    短期予報（3日間）または週間予報（7日間）を選択できます。

    Args:
        prefecture_name: 都道府県名（例: "東京", "東京都", "大阪", "北海道"）
        forecast_type: 予報の種類。"short"（短期・3日間）または "weekly"（週間・7日間）

    Returns:
        JSON形式の天気予報データ（文字列）。以下の情報を含みます：
        - 地域名と地域コード
        - 発表日時
        - 日時ごとの天気、天気コード、天気説明
        - 風、波の情報
        - 降水確率、気温（最高・最低）

    Raises:
        ValueError: 都道府県名が見つからない場合
        Exception: APIからのデータ取得に失敗した場合

    Examples:
        >>> get_weather_forecast("東京", "short")
        >>> get_weather_forecast("大阪府", "weekly")
    """
    try:
        # 都道府県名から地域コードを取得
        prefecture_code = _find_prefecture_code(prefecture_name)

        # 予報データを取得
        forecast_url = f"https://www.jma.go.jp/bosai/forecast/data/forecast/{prefecture_code}.json"
        forecast_data = _fetch_json(forecast_url)

        # データを整形
        formatted_data = _format_forecast_data(forecast_data, forecast_type)

        # 短期予報の場合は最初の3日分のみ、週間予報の場合は全て
        if forecast_type == "short":
            # 短期予報として最初の3日分に絞る
            for area in formatted_data["areas"]:
                area["forecasts"] = area["forecasts"][:3]

        return json.dumps(formatted_data, ensure_ascii=False, indent=2)

    except ValueError as e:
        return json.dumps({
            "error": str(e),
            "hint": "都道府県名を確認してください。例: 東京、東京都、北海道、大阪、大阪府"
        }, ensure_ascii=False, indent=2)
    except Exception as e:
        return json.dumps({
            "error": f"天気予報の取得に失敗しました: {str(e)}"
        }, ensure_ascii=False, indent=2)