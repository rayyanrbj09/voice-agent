import requests
from bs4 import BeautifulSoup


def decode_secret_message(url):
    response = requests.get(url)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    points = []

    for row in soup.find_all("tr"):
        cells = row.find_all(["td", "th"])

        if len(cells) < 3:
            continue

        values = [cell.get_text(strip=True) for cell in cells]

        try:
            x = int(values[1])
            y = int(values[2])
        except ValueError:
            continue

        points.append((x, y, values[0]))

    if not points:
        return

    max_x = max(point[0] for point in points)
    max_y = max(point[1] for point in points)

    grid = [[" " for _ in range(max_x + 1)] for _ in range(max_y + 1)]

    for x, y, char in points:
        grid[y][x] = char

    for row in grid:
        print("".join(row))