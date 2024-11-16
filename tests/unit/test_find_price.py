import pytest
from bs4 import BeautifulSoup
from UniversalWebshopScraper.generalized_scrapper.core.generalized_scrapper import GeneralizedScraper


@pytest.fixture
def scraper():
    """
    Create an instance of the GeneralizedScraper class in offline mode for testing.
    """
    return GeneralizedScraper(offline_mode=True)


@pytest.mark.parametrize(
    "html_input, expected_price",
    [
        # Test case 1: Single block with a price
        (
            """<div><span>100</span><span>.99</span><span>$</span></div>""",
            "100.99$"
        ),
        # Test case 2: Noise text with price
        (
            """<div><span>Inteligentne zegarki Fitness Tracker IP 68,</span><span>100</span><span>$</span></div>""",
            "100$"
        ),
        # Test case 3: Complex price format
        (
            """<div><span>Special offer: </span><span>1,000</span><span>.50</span><span>USD</span></div>""",
            "1,000.50USD"
        ),
        # Test case 4: No price present
        (
            """<div><span>No price available</span></div>""",
            None
        ),
        # Test case 5: real-world example with price
        (
            """<div class="msa3_z4 m3h2_8"><span aria-label="437,70&nbsp;zł aktualna cena" tabindex="0"><span class="mli8_k4 msa3_z4 mqu1_1 mp0t_ji m9qz_yo mgmw_qw mgn2_27 mgn2_30_s">437,<span class="mgn2_19 mgn2_21_s m9qz_yq">70</span>&nbsp;<span class="mgn2_19 mgn2_21_s m9qz_yq">zł</span></span></span></div>""",
            "437,70zł"
        ),
        # Test case 6: real-world example with price
        (
            """<article class="mx7m_1 mnyp_co mlkp_ag"><div class="mqen_m6 mjyo_6x mgmw_3z mpof_ki mwdn_0 mp7g_oh mj7a_16 mg9e_16 mh36_16 mh36_24_l mvrt_16 mvrt_24_l m7er_k4 m0ux_vh mp5q_jr m31c_kb _1e32a_ENO3Q"><div class="mvrt_8 mse2_k4"><div><div class="mp7g_oh"><a href="https://allegro.pl/oferta/samsung-qe65q77da-tv-qled-4k-smart-tv-tizen-dvb-t2-15882324916" rel="nofollow" aria-hidden="true" tabindex="-1" class="msts_9u mg9e_0 mvrt_0 mj7a_0 mh36_0 mpof_ki m389_6m mx4z_6m m7f5_6m _1e32a_7ZEQF"><img alt="Telewizor Samsung QE65Q77DATXXH 65&quot; QLED 4K UHD" loading="lazy" src="https://a.allegroimg.com/s180/1173cc/b8bbf6ad4a1b98d7d821fc5dbd87/Samsung-QE65Q77DA-TV-Qled-4K-Smart-TV-Tizen-DVB-T2" srcset="https://a.allegroimg.com/s180/1173cc/b8bbf6ad4a1b98d7d821fc5dbd87/Samsung-QE65Q77DA-TV-Qled-4K-Smart-TV-Tizen-DVB-T2 1x, https://a.allegroimg.com/s720/1173cc/b8bbf6ad4a1b98d7d821fc5dbd87/Samsung-QE65Q77DA-TV-Qled-4K-Smart-TV-Tizen-DVB-T2 2x"></a><div class="mpof_ki m389_6m mp7g_f6 mqm6_0 mj7u_0"><a data-analytics-interaction="true" data-analytics-interaction-label="energyLabel" class="mpof_ki"><img src="https://assets.allegrostatic.com/showoffer-icons-external/EFFICIENCY_CLASS_E.svg" alt="Etykieta energetyczna" class="m3h2_8 _1e32a_78N6o"></a></div></div><div class="mzmg_6m mgn2_12 mgmw_3z mp4t_8">dostępne warianty</div></div></div><div class="mpof_ki mr3m_1 myre_zn myre_8v_l _1e32a_pAK3c"><div class="mjyo_6x mpof_ki myre_zn mj7a_8 mj7a_0_l mvrt_8_l m7er_k4 _1e32a_PH-oM"><div class="_1e32a_WGU9V mryx_16"><h2 class="mgn2_14 m9qz_yp mqu1_16 mp4t_0 m3h2_0 mryx_0 munh_0"><a href="https://allegro.pl/oferta/samsung-qe65q77da-tv-qled-4k-smart-tv-tizen-dvb-t2-15882324916" class="mgn2_14 mp0t_0a mgmw_wo mj9z_5r mli8_k4 mqen_m6 l1qs9 l1jot meqh_en mpof_z0 mqu1_16 m6ax_n4 _1e32a_f18Kx ">Telewizor Samsung QE65Q77DATXXH 65" QLED 4K UHD</a></h2><div class="mg9e_4 mpof_ki myre_zn m389_5x"><div aria-label="5,00 na 5, 42 oceny produktu" role="group" class="mpof_vs mgn2_12 mqu1_g3 mgmw_3z"><span aria-hidden="true" class="m9qz_yq mgmw_wo">5,00</span><div aria-hidden="true" class="mpof_vs mjru_k4 mpof_vs mjru_k4 _1e32a_CoJOu m7er_80 mp4t_0 m3h2_4 mryx_0 munh_4 _1e32a_n4afv"><div class="mpof_vs mjru_k4 mpof_vs mjru_k4 _1e32a_CoJOu m7er_80 _1e32a_7GNWA" style="width: 100%;"></div></div><span aria-hidden="true" class="mpof_uk">(42)</span></div><div class="mpof_vs mgn2_12 mqu1_g3 mgmw_3z mg9e_2"><div class="mp7g_oh "><div class="mgn2_12 mpof_ki m389_6m mwdn_1"><div class="mpof_ki m389_6m mwdn_1 _1e32a_x7RE- m3h2_0"><span class="mli2_0" style="color: rgb(34, 34, 34); font-weight: bold; text-decoration: none;">180 osób</span><span class="mli2_0" style="color: var(--m-color-text-secondary, #656565); font-weight: normal; text-decoration: none;">kupiło ostatnio</span></div></div><div class="mpof_5r mpof_3f_l mpof_3f"><div class="mjyo_6x mp7g_f6 mjb5_w6 msbw_2 mldj_2 mtag_2 mm2b_2 mgmw_wo msts_n6 m7er_k4 ti1554 ti1nw9 mpof_5r undefined"></div></div></div></div></div><div class="mpof_z0 m7er_k4 mg9e_4 mj7a_4"><div class="mgn2_12"><div><span class="mgmw_3z _1e32a_XFNn4">Smart TV</span> <span class="mgmw_wo mvrt_8 ">Tizen</span> <span class="mgmw_3z _1e32a_XFNn4">Liczba złączy HDMI</span> <span class="mgmw_wo mvrt_8 ">4</span> <span class="mgmw_3z _1e32a_XFNn4">Klasa efektywności energetycznej</span> <span class="mgmw_wo mvrt_8 ">E</span> <span class="mgmw_3z _1e32a_XFNn4">Szerokość produktu z podstawą</span> <span class="mgmw_wo mvrt_8 ">145.17 cm</span> <span class="mgmw_3z _1e32a_XFNn4">Wysokość produktu z podstawą</span> <span class="mgmw_wo mvrt_8 ">89.75 cm</span> <span class="mgmw_3z _1e32a_XFNn4">Głębokość produktu z podstawą</span> <span class="mgmw_wo mvrt_8 ">29.02 cm</span> <span class="mgmw_3z _1e32a_XFNn4">Szerokość produktu</span> <span class="mgmw_wo mvrt_8 ">1455.17 cm</span> <span class="mgmw_3z _1e32a_XFNn4">Wysokość produktu</span> <span class="mgmw_wo mvrt_8 ">83.18 cm</span> </div></div></div><p class="mp4t_0 m3h2_0 mryx_0 munh_0 meqh_en m6ax_n4 mgn2_12 msa3_z4 _1e32a_3NbHx"><span>Produkt:</span> <a href="https://allegro.pl/produkt/telewizor-samsung-qe65q77datxxh-65-qled-4k-uhd-01e02367-9542-4210-8378-da901bbb1bc9" title="Telewizor Samsung QE65Q77DATXXH 65&quot; QLED 4K UHD" target="_self" class="mj9z_5r _1e32a_KBSWp">Telewizor Samsung QE65Q77DATXXH 65" QLED 4K UHD</a></p><div class="mpof_ki m389_6m "><a data-analytics-interaction="true" data-analytics-interaction-label="informationSheet" class="mgmw_3z msa3_z4 mj9z_5r mgn2_12"></a></div></div><div class="mp4t_56 mpof_ki myre_zn m389_5x"><a href="https://allegro.pl/produkt/telewizor-samsung-qe65q77datxxh-65-qled-4k-uhd-01e02367-9542-4210-8378-da901bbb1bc9?ocoi=ai9icVllMTdiZDg5d3FlamxWNFE4VEtnU3JmOHI3b0I%3D" data-role-type="product-fiche-link" data-onboarding-hook="product_fiche" rel="nofollow" target="_self" class="mp0t_0a m9qz_yp mp7g_oh mtsp_ib mli8_k4 mp4t_0 m3h2_0 mryx_0 munh_0 msbw_rf mldj_rf mtag_rf mm2b_rf mqvr_2 mqen_m6 m0qj_5r msts_n7 mh36_16 mvrt_16 mg9e_8 mj7a_8 mjir_sv m2ha_2 m8qd_vz mjt1_n2 m09p_40 bfwvy mgmw_u5g mrmn_qo mrhf_u8 m31c_kb m0ux_fp b14a0 mzmg_6m mjru_k4 mgn2_14 m6ax_n4 meqh_en msa3_z4 mjyo_6x m911_co mefy_co mnyp_co mdwl_co mx7m_1 mpof_ki m389_6m m7f5_6m _1e32a_jptRV">porównaj 24 oferty</a></div></div><div class="m911_co mpof_ki myre_zn m7f5_5x mg9e_8 mg9e_0_l mh36_16_l mx7m_1 mlkp_ag m7er_k4 _1e32a_WSqB7"><div class="mpof_ki"><div class="_1e32a_WGU9V mzaq_56"><div class="_1e32a_62rFQ"><div></div></div><div class="mj7a_4 mg9e_4 _1e32a_IAwmj"><div class="mpof_ki m389_0a mwdn_1"><div class="msa3_z4 m3h2_8"><span aria-label="3649,00&nbsp;zł aktualna cena" tabindex="0"><span class="mli8_k4 msa3_z4 mqu1_1 mp0t_ji m9qz_yo mgmw_qw mgn2_27 mgn2_30_s">3649,<span class="mgn2_19 mgn2_21_s m9qz_yq">00</span>&nbsp;<span class="mgn2_19 mgn2_21_s m9qz_yq">zł</span></span></span></div><span class="mpof_92 mp7g_oh"><div class="mp7g_oh "><div class="mgn2_12 mpof_ki m389_6m mwdn_1"><div class="mpof_ki m389_6m mwdn_1 _1e32a_x7RE- m3h2_0"><picture><source media="(prefers-color-scheme: dark)" srcset="https://a.allegroimg.com/original/34611c/c433ab0c4bf9a76e4f1f15b5dd1f/dark-brand-subbrand-smart-2ecf1fa38c.svg"><img src="https://a.allegroimg.com/original/343b4d/ed3f5c04412ab7bd70dd0a34f0cd/brand-subbrand-smart-d8bfa93f10.svg" alt="Smart!" class="mpof_z0 _1e32a_ELS6C"></picture></div></div><div class="mpof_5r mpof_3f_l "><div class="mjyo_6x mp7g_f6 mjb5_w6 msbw_2 mldj_2 mtag_2 mm2b_2 mgmw_wo msts_n6 m7er_k4 ti1554 ti1nw9 mpof_5r undefined"></div></div></div></span></div></div><div class="mqu1_g3 mgn2_12">darmowa dostawa</div></div><div class="mpof_ki myre_zn m389_0a mjyo_6x mvrt_4 _1e32a_LT2ZR"><div class="mh36_0"><div class="mzmg_f9"><span class="mgmw_3z mpof_z0 mgn2_12">Firma</span></div></div></div></div><div class="_1e32a_WGU9V mg9e_4"><div class="mgn2_12 mpof_ki m389_6m mwdn_1"><div class="mpof_ki m389_6m mwdn_1 m3h2_4 _1e32a_x7RE-"><span class="mli2_0" style="color: var(--m-color-text-secondary, #656565); font-weight: bold; text-decoration: none;">243,27&nbsp;zł</span><span class="mli2_0" style="color: var(--m-color-text-secondary, #656565); font-weight: normal; text-decoration: none;"> x 15 rat</span></div><div class="msbw_2 mldj_2 mtag_2 mm2b_2 mgmw_3z mp0t_ji mh36_4 mvrt_4 mj7a_2 mg9e_2 m3h2_4 _1e32a_-sT7n" style="background-color: rgb(0, 174, 239); color: rgb(255, 255, 255);"><span class="mli2_0">raty&nbsp;zero</span></div><div class="mpof_ki m389_6m mwdn_1 _1e32a_x7RE- m3h2_0"><span class="mli2_0" style="color: var(--m-color-text-secondary, #656565); font-weight: normal; text-decoration: none;">sprawdź</span></div></div><div><div class="mgn2_12"><div><span class="mgmw_3z _1e32a_XFNn4">Stan</span> <span class="mgmw_wo mvrt_8 ">Nowy</span> </div></div></div><div class="mgn2_12 mpof_ki m389_6m mwdn_1"><div class="mpof_ki m389_6m mwdn_1 _1e32a_x7RE- m3h2_0"><span class="mli2_0" style="color: var(--m-color-text-secondary, #656565); font-weight: bold; text-decoration: none;">dostawa do czw. 21 lis.</span><div class="mp7g_oh "><picture><source media="(prefers-color-scheme: dark)" srcset="https://assets.allegrostatic.com/fast-delivery-icons/information-dark.svg"><img src="https://assets.allegrostatic.com/fast-delivery-icons/information.svg" alt="" class="mpof_z0 _1e32a_ELS6C"></picture><div class="mpof_5r mpof_3f_l mpof_3f"><div class="mjyo_6x mp7g_f6 mjb5_w6 msbw_2 mldj_2 mtag_2 mm2b_2 mgmw_wo msts_n6 m7er_k4 ti1554 ti1nw9 mpof_5r undefined"></div></div></div></div></div></div><div class="mpof_ki m7f5_0a mjyo_6x mzaq_1 mr3m_0 mp4t_56 mg9e_16 mvrt_4 mzmg_6m m7er_k4"><button data-role-type="add-to-cart-button" class="mgn2_14 mp0t_0a m9qz_yp mp7g_oh mtsp_ib mli8_k4 mp4t_0 mryx_0 munh_0 m911_5r mefy_5r mnyp_5r mdwl_5r msbw_rf mldj_rf mtag_rf mm2b_rf mqvr_2 mqen_m6 meqh_en m0qj_5r mh36_16 mvrt_16 mg9e_8 mj7a_8 mjir_sv m2ha_2 m8qd_vz mjt1_n2 m09p_40 bfwvy mgmw_yu msts_er mrmn_qo mrhf_u8 m31c_kb m0ux_fp b14ge mzaq_1 mzmg_6m m7er_k4 m3h2_8"><span>dodaj do koszyka</span></button><button aria-label="Dodaj do ulubionych" class="m7er_40 mp0t_0a m9qz_yp mp7g_oh mtsp_ib mli8_k4 mp4t_0 m3h2_0 mryx_0 munh_0 m911_5r mefy_5r mnyp_5r mdwl_5r msbw_rf mldj_rf mtag_rf mm2b_rf mqvr_2 mqen_m6 meqh_en m0qj_5r msts_n7 mjir_sv m2ha_2 m8qd_vz mjt1_n2 m09p_40 bfwvy mgmw_u5g mrmn_qo mrhf_u8 m31c_kb m0ux_fp b14a0 mqu1_1 mgn2_13 mg9e_0 mvrt_0 mj7a_0 mh36_0 mse2_40"><picture><source media="(prefers-color-scheme: dark)" srcset="https://a.allegroimg.com/original/34da48/7daf74174cbab949125433930aba/dark-action-common-heart-d21a0d364b"><img src="https://a.allegroimg.com/original/342704/5df50ccf415c9dc190264897d100/action-common-heart-322d64f02b" alt="" aria-hidden="true" class="mjyo_6x meqh_en msa3_z4 mhd5_0m i150e mse2_40 mg9e_4 mvrt_4 mj7a_4 mh36_4 m0s5_ki"></picture></button></div></div></div></div></article>""",
            "3649,00zł"
        ),
    ],
)

def test_find_price(scraper, html_input, expected_price):
    """
    Test the find_price function from GeneralizedScraper.
    """
    soup = BeautifulSoup(html_input, "html.parser")
    block = soup.div  # Assume we're testing the <div> block

    # Call the find_price function
    detected_price = scraper.find_price(block)

    # Assert the output matches the expected price
    assert detected_price == expected_price
