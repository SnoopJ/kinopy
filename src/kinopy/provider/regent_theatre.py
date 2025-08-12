import json
from collections import defaultdict
from datetime import date
from urllib.parse import unquote

import lxml.html

from ..datamodel import CACHE_ROOT, Showing
from ..util import daily_cache, web


CACHE = CACHE_ROOT.joinpath("RegentTheatre")
CACHE.mkdir(exist_ok=True, parents=True)


class RegentTheatreProvider:
    JSON_URL = "https://regenttheatre.com/?evo-ajax=eventon_init_load"
    EVENTON_PAYLOAD_PATTERN = {
        "global[calendars][]": "EVOFC",
        "cals[evcal_calendar_685][sc][accord]": "no",
        "cals[evcal_calendar_685][sc][bottom_nav]": "no",
        "cals[evcal_calendar_685][sc][cal_id]": "",
        "cals[evcal_calendar_685][sc][cal_init_nonajax]": "no",
        "cals[evcal_calendar_685][sc][calendar_type]": "fullcal",
        "cals[evcal_calendar_685][sc][day_incre]": "0",
        "cals[evcal_calendar_685][sc][ehover]": "def",
        "cals[evcal_calendar_685][sc][ep_fields]": "",
        "cals[evcal_calendar_685][sc][etc_override]": "no",
        "cals[evcal_calendar_685][sc][evc_open]": "yes",
        "cals[evcal_calendar_685][sc][event_count]": "0",
        "cals[evcal_calendar_685][sc][event_location]": "all",
        "cals[evcal_calendar_685][sc][event_order]": "ASC",
        "cals[evcal_calendar_685][sc][event_organizer]": "all",
        "cals[evcal_calendar_685][sc][event_parts]": "no",
        "cals[evcal_calendar_685][sc][event_past_future]": "all",
        "cals[evcal_calendar_685][sc][event_status]": "all",
        "cals[evcal_calendar_685][sc][event_tag]": "all",
        "cals[evcal_calendar_685][sc][event_type]": "all",
        "cals[evcal_calendar_685][sc][event_type_2]": "all",
        "cals[evcal_calendar_685][sc][event_virtual]": "all",
        "cals[evcal_calendar_685][sc][eventtop_date_style]": "0",
        "cals[evcal_calendar_685][sc][eventtop_style]": "3",
        "cals[evcal_calendar_685][sc][exp_jumper]": "no",
        "cals[evcal_calendar_685][sc][exp_so]": "no",
        "cals[evcal_calendar_685][sc][filter_relationship]": "AND",
        "cals[evcal_calendar_685][sc][filter_show_set_only]": "no",
        "cals[evcal_calendar_685][sc][filter_style]": "default",
        "cals[evcal_calendar_685][sc][filter_type]": "default",
        "cals[evcal_calendar_685][sc][filters]": "yes",
        # NOTE: the following are meant to be populated before sending the request. I don't think the focus values have
        # any effect on the retrieval of backend data, but the fixed_* values do
        "cals[evcal_calendar_685][sc][fixed_day]": None,
        "cals[evcal_calendar_685][sc][fixed_month]": None,
        "cals[evcal_calendar_685][sc][fixed_year]": None,
        "cals[evcal_calendar_685][sc][focus_end_date_range]": None,
        "cals[evcal_calendar_685][sc][focus_start_date_range]": None,
        "cals[evcal_calendar_685][sc][ft_event_priority]": "no",
        "cals[evcal_calendar_685][sc][grid_ux]": "2",
        "cals[evcal_calendar_685][sc][heat]": "no",
        "cals[evcal_calendar_685][sc][hide_arrows]": "no",
        "cals[evcal_calendar_685][sc][hide_cancels]": "no",
        "cals[evcal_calendar_685][sc][hide_empty_months]": "no",
        "cals[evcal_calendar_685][sc][hide_end_time]": "no",
        "cals[evcal_calendar_685][sc][hide_et_dn]": "no",
        "cals[evcal_calendar_685][sc][hide_et_extra]": "no",
        "cals[evcal_calendar_685][sc][hide_et_tags]": "no",
        "cals[evcal_calendar_685][sc][hide_et_tl]": "no",
        "cals[evcal_calendar_685][sc][hide_ft]": "no",
        "cals[evcal_calendar_685][sc][hide_ft_img]": "no",
        "cals[evcal_calendar_685][sc][hide_month_headers]": "no",
        "cals[evcal_calendar_685][sc][hide_mult_occur]": "no",
        "cals[evcal_calendar_685][sc][hide_past]": "no",
        "cals[evcal_calendar_685][sc][hide_past_by]": "ee",
        "cals[evcal_calendar_685][sc][hide_so]": "no",
        "cals[evcal_calendar_685][sc][hide_sort_options]": "no",
        "cals[evcal_calendar_685][sc][hover]": "numname",
        "cals[evcal_calendar_685][sc][ics]": "no",
        "cals[evcal_calendar_685][sc][jumper]": "yes",
        "cals[evcal_calendar_685][sc][jumper_count]": "5",
        "cals[evcal_calendar_685][sc][jumper_offset]": "0",
        "cals[evcal_calendar_685][sc][lang]": "L1",
        "cals[evcal_calendar_685][sc][layout_changer]": "no",
        "cals[evcal_calendar_685][sc][livenow_bar]": "yes",
        "cals[evcal_calendar_685][sc][load_fullmonth]": "yes",
        "cals[evcal_calendar_685][sc][mapformat]": "roadmap",
        "cals[evcal_calendar_685][sc][mapiconurl]": "",
        "cals[evcal_calendar_685][sc][maps_load]": "yes",
        "cals[evcal_calendar_685][sc][mapscroll]": "true",
        "cals[evcal_calendar_685][sc][mapzoom]": "18",
        "cals[evcal_calendar_685][sc][members_only]": "no",
        "cals[evcal_calendar_685][sc][ml_priority]": "no",
        "cals[evcal_calendar_685][sc][ml_toend]": "no",
        "cals[evcal_calendar_685][sc][mo1st]": "",
        "cals[evcal_calendar_685][sc][month_incre]": "0",
        "cals[evcal_calendar_685][sc][nexttogrid]": "no",
        "cals[evcal_calendar_685][sc][number_of_months]": "1",
        "cals[evcal_calendar_685][sc][only_ft]": "no",
        "cals[evcal_calendar_685][sc][pec]": "",
        "cals[evcal_calendar_685][sc][s]": "",
        "cals[evcal_calendar_685][sc][search]": "",
        "cals[evcal_calendar_685][sc][search_all]": "no",
        "cals[evcal_calendar_685][sc][sep_month]": "no",
        "cals[evcal_calendar_685][sc][show_et_ft_img]": "yes",
        "cals[evcal_calendar_685][sc][show_limit]": "no",
        "cals[evcal_calendar_685][sc][show_limit_ajax]": "no",
        "cals[evcal_calendar_685][sc][show_limit_paged]": "1",
        "cals[evcal_calendar_685][sc][show_limit_redir]": "",
        "cals[evcal_calendar_685][sc][show_repeats]": "no",
        "cals[evcal_calendar_685][sc][show_search]": "no",
        "cals[evcal_calendar_685][sc][show_upcoming]": "0",
        "cals[evcal_calendar_685][sc][show_year]": "no",
        "cals[evcal_calendar_685][sc][social_share]": "no",
        "cals[evcal_calendar_685][sc][sort_by]": "sort_date",
        "cals[evcal_calendar_685][sc][style]": "def",
        "cals[evcal_calendar_685][sc][tile_bg]": "0",
        "cals[evcal_calendar_685][sc][tile_bg_size]": "full",
        "cals[evcal_calendar_685][sc][tile_count]": "2",
        "cals[evcal_calendar_685][sc][tile_height]": "0",
        "cals[evcal_calendar_685][sc][tile_style]": "0",
        "cals[evcal_calendar_685][sc][tiles]": "no",
        "cals[evcal_calendar_685][sc][ux_val]": "0",
        "cals[evcal_calendar_685][sc][view_switcher]": "no",
        "cals[evcal_calendar_685][sc][wpml_l1]": "",
        "cals[evcal_calendar_685][sc][wpml_l2]": "",
        "cals[evcal_calendar_685][sc][wpml_l3]": "",
        "cals[evcal_calendar_685][sc][yl_priority]": "no",
        "cals[evcal_calendar_685][sc][yl_toend]": "no",
        "cals[evcal_calendar_685][sc][_cver]": "4.9.11",
        # NOTE: I am not sure if this nonce actually changes
        "nonce": "95e6b2f613"
    }

    @classmethod
    @daily_cache(cachedir=CACHE, json=True)
    def showings_by_date(cls, from_date: date, to_date: date) -> dict[date, list[Showing]]:
        shows = cls.showings_json(from_date=from_date, to_date=to_date)
        results = defaultdict(list)

        for event_ID, shw in shows.items():
            dt = date.fromtimestamp(shw["event_start_unix"])
            if not (from_date <= dt <= to_date):
                # NOTE:the API seems to serve an entire month at a time with the above query parameters, so we just filter
                # them here
                continue

            # TODO: unescape?
            title = shw["event_title"]
            # NOTE: There seems to be no good way to link directly to a showing using the JSON data, but maybe it can
            # be scraped out of the HTML contained in the JSON data (yeesh), at least for events that have only one link.
            # Seems that event cards for festivals have multiple links, so the safest thing to do feels like to link to
            # their schedule landing page and let the user sort it out :(
            url = "https://regenttheatre.com/schedule/"
            excerpt = None

            s = Showing(
                date=str(dt),
                title=title,
                url=url,
                excerpt=excerpt,
            )
            results[dt].append(s)

        return results

    @classmethod
    def showings_json(cls, from_date: date, to_date: date) -> dict[int, dict]:
        content = cls.schedule_json(from_date=from_date, to_date=to_date)
        result = {shw["event_id"]: shw for shw in content["cals"]["evcal_calendar_685"]["json"]}

        # NOTE: [insert heavy sigh here]
        # So, the Regent has plenty of events that aren't movies, and I don't want to show them on this calendar, so
        # it's necessary to get the event types. HOWEVER, this data is not available in the JSON data extracted above
        # (as far as I can tell), but ONLY encoded in the resulting HTML that is also included in the response. So, we
        # have to go spelunking in order to retrieve some of this information
        doc = lxml.html.fromstring(content["cals"]["evcal_calendar_685"]["html"])

        for event_root in doc.xpath("//div[@data-time]"):
            start, stop = (date.fromtimestamp(int(val)) for val in event_root.attrib["data-time"].split('-'))
            event_id = int(event_root.attrib["data-event_id"])
            [title] = [node.text_content() for node in event_root.xpath(".//span[contains(@class, 'evoet_title')]")]
            tags = [node.text_content().strip(",").lower() for node in event_root.xpath(".//em[@data-tagid]")]
            if "movie" not in tags:
                # NOTE:Some events will appear multiple times in the resulting HTML so we have to look before we delete
                if event_id in result:
                    print(f"Not a movie, removing: {title!r} ({start.isoformat()})")
                    result.pop(event_id)

        return result

    @classmethod
    def schedule_json(cls, from_date: date, to_date: date) -> dict:
        url = cls.JSON_URL
        payload = cls.EVENTON_PAYLOAD_PATTERN.copy()
        payload["cals[evcal_calendar_685][sc][fixed_day]"] = str(from_date.day)
        payload["cals[evcal_calendar_685][sc][fixed_month]"] = str(from_date.month)
        payload["cals[evcal_calendar_685][sc][fixed_year]"] = str(from_date.year)
        payload["cals[evcal_calendar_685][sc][focus_start_date_range]"] = from_date.strftime('%s')
        payload["cals[evcal_calendar_685][sc][focus_end_date_range]"] = to_date.strftime('%s')

        response = web.post(url, data=payload)
        response.raise_for_status()

        result = response.json()

        return result
