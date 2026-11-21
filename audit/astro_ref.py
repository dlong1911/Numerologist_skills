"""Independent astrology references from JPL DE421 via Skyfield (no Swiss Ephemeris code)."""
import math
from pathlib import Path
from skyfield.api import Loader
from skyfield.framelib import ecliptic_frame
from skyfield.nutationlib import iau2000a_radians, mean_obliquity

_L = Loader(str(Path(__file__).parent / "jpl"))
EPH = _L("de421.bsp")
TS = _L.timescale(builtin=True)
EARTH = EPH["earth"]
BODIES = {"Sun": "sun", "Moon": "moon", "Mercury": "mercury", "Venus": "venus", "Mars": "mars",
          "Jupiter": "jupiter barycenter", "Saturn": "saturn barycenter", "Uranus": "uranus barycenter",
          "Neptune": "neptune barycenter", "Pluto": "pluto barycenter"}


def t_of(utc):
    """Treat civil UTC as UT1 (|UT1-UTC| < 0.9 s); avoids Skyfield's pre-1972 UTC model."""
    u = utc.astimezone(__import__("datetime").timezone.utc)
    return TS.ut1(u.year, u.month, u.day, u.hour, u.minute, u.second + u.microsecond / 1e6)


def lon(name, t):
    """Apparent geocentric longitude, true ecliptic & equinox of date."""
    lat_, lon_, _ = EARTH.at(t).observe(EPH[BODIES[name]]).apparent().frame_latlon(ecliptic_frame)
    return lon_.degrees % 360


def speed(name, t):
    dt = 1 / 24
    a, b = lon(name, TS.tt_jd(t.tt - dt)), lon(name, TS.tt_jd(t.tt + dt))
    return ((b - a + 180) % 360 - 180) / (2 * dt)


def true_obliquity(t):
    d_psi, d_eps = iau2000a_radians(t)
    return math.radians(mean_obliquity(t.tdb) / 3600) + d_eps


def angles(t, lat_deg, lon_deg):
    """ASC, MC, RAMC, eps (degrees) from apparent sidereal time + true obliquity."""
    eps = true_obliquity(t)
    ramc = math.radians((t.gast * 15 + lon_deg) % 360)
    phi = math.radians(lat_deg)
    mc = math.degrees(math.atan2(math.sin(ramc), math.cos(ramc) * math.cos(eps))) % 360
    asc = math.degrees(math.atan2(math.cos(ramc), -(math.sin(ramc) * math.cos(eps) + math.tan(phi) * math.sin(eps)))) % 360
    return asc, mc, math.degrees(ramc), math.degrees(eps)


def placidus(t, lat_deg, lon_deg):
    """Cusps 1..12 by Placidus semi-arc trisection (iterative)."""
    asc, mc, ramc, eps_d = angles(t, lat_deg, lon_deg)
    eps, phi = math.radians(eps_d), math.radians(lat_deg)

    def lam_from_ra(ra):
        ra = math.radians(ra)
        return math.degrees(math.atan2(math.sin(ra), math.cos(ra) * math.cos(eps))) % 360

    def ad_of(lam):
        dec = math.asin(math.sin(eps) * math.sin(math.radians(lam)))
        return math.degrees(math.asin(max(-1, min(1, math.tan(phi) * math.tan(dec)))))

    def cusp(f, above):
        ra = ramc + (30 if above else 150) * (1 if f == 1 else 2)
        for _ in range(100):
            lam = lam_from_ra(ra)
            ad = ad_of(lam)
            ra = ramc + f * (90 + ad) / 3 if above else ramc + 180 - f * (90 - ad) / 3
        return lam_from_ra(ra)

    c11, c12 = cusp(1, True), cusp(2, True)
    c3, c2 = cusp(1, False), cusp(2, False)
    c = [asc, c2, c3, (mc + 180) % 360, (c11 + 180) % 360, (c12 + 180) % 360,
         (asc + 180) % 360, (c2 + 180) % 360, (c3 + 180) % 360, mc, c11, c12]
    return c


def mean_node(t):
    T = (t.tt - 2451545.0) / 36525
    return (125.0445479 - 1934.1362891 * T + 0.0020754 * T ** 2 + T ** 3 / 467441 - T ** 4 / 60616000) % 360


def true_node(t):
    """Osculating ascending node of the geocentric lunar orbit, ecliptic of date."""
    (x, y, z), (vx, vy, vz) = [a.au if hasattr(a, "au") else a.au_per_d for a in
                               (EPH["moon"] - EARTH).at(t).frame_xyz_and_velocity(ecliptic_frame)]
    hx, hy = y * vz - z * vy, z * vx - x * vz
    return math.degrees(math.atan2(hx, -hy)) % 360


def sun_altitude(t, lat_deg, lon_deg):
    from skyfield.api import wgs84
    obs = EARTH + wgs84.latlon(lat_deg, lon_deg)
    alt, _, _ = obs.at(t).observe(EPH["sun"]).apparent().altaz()
    return alt.degrees
