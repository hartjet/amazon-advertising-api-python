from amazon_advertising_api.regions import regions
from amazon_advertising_api.versions import versions
from io import BytesIO
try:
    # Python 3
    import urllib.request
    import urllib.parse
    PYTHON = 3
except ImportError:
    # Python 2
    from six.moves import urllib
    PYTHON = 2
import gzip
import json


class AdvertisingApiV3(object):
    """Lightweight client library for Amazon Sponsored Products API."""

    def __init__(self,
                 client_id,
                 client_secret,
                 region,
                 profile_id=None,
                 access_token=None,
                 refresh_token=None,
                 sandbox=False):
        """
        Client initialization.

        :param client_id: Application client Id that has been whitelisted
            for cpc_advertising:campaign_management
        :type client_id: string
        :param client_secret: Application client secret key.
        :type client_id: string
        :param region: Region code for endpoint. See regions.py.
        :type region: string
        :param access_token: The access token for the advertiser account. Optional
        :type access_token: string
        :param refresh_token: The refresh token for the advertiser account.
        :type refresh_token: string
        :param sandbox: Indicate whether you are operating in sandbox or prod.
        :type sandbox: boolean
        """
        self.client_id = client_id
        self.client_secret = client_secret
        self._access_token = access_token
        self.refresh_token = refresh_token

        self.api_version = versions['api_version']
        self.user_agent = 'AdvertisingAPI Python Client Library v{}'.format(
            versions['application_version'])
        self.profile_id = profile_id
        self.token_url = None
        self.sandbox = sandbox

        if region in regions:
            if sandbox:
                self.endpoint = regions[region]['sandbox']
            else:
                self.endpoint = regions[region]['prod']
            self.token_url = regions[region]['token_url']
        else:
            raise KeyError('Region {} not found in regions.'.format(region))

    @property
    def access_token(self):
        return self._access_token

    @access_token.setter
    def access_token(self, value):
        """Set access_token"""
        self._access_token = value

    def do_refresh_token(self):
        if self.refresh_token is None:
            return {'success': False,
                    'code': 0,
                    'response': 'refresh_token is empty.'}

        if self._access_token:
            self._access_token = urllib.parse.unquote(self._access_token)
        self.refresh_token = urllib.parse.unquote(self.refresh_token)

        params = {
            'grant_type': 'refresh_token',
            'refresh_token': self.refresh_token,
            'client_id': self.client_id,
            'client_secret': self.client_secret}

        data = urllib.parse.urlencode(params)

        req = urllib.request.Request(
            url='https://{}'.format(self.token_url),
            data=data.encode('utf-8'))

        try:
            f = urllib.request.urlopen(req)
            response = f.read().decode('utf-8')
            if 'access_token' in response:
                json_data = json.loads(response)
                self._access_token = json_data['access_token']
                return {'success': True,
                        'code': f.code,
                        'response': self._access_token}
            else:
                return {'success': False,
                        'code': f.code,
                        'response': 'access_token not in response.'}
        except urllib.error.HTTPError as e:
            return {'success': False,
                    'code': e.code,
                    'response': '{msg}: {details}'.format(msg=e.msg, details=e.read())}

    """ *********************************************************************
    PROFILE MANAGEMENT
    ********************************************************************* """
    def register_profile(self, country_code):
        """
        Registers a sandbox profile.
        """
        interface = 'profiles/register'
        params = {"countryCode": country_code}
        return self._operation(interface, params, method='PUT')

    def list_profiles(self):
        interface = 'profiles'
        return self._operation(interface)

    def get_profile(self, profile_id):
        interface = 'profiles/{}'.format(profile_id)
        return self._operation(interface)

    def update_profiles(self, data):
        interface = 'profiles'
        return self._operation(interface, data, method='PUT')

    """ *********************************************************************
    PORTFOLIO MANAGEMENT
    ********************************************************************* """
    def list_portfolios(self, data=None, extended=False):
        interface = 'portfolios{}'.format('/extended' if extended else '')
        return self._operation(interface, data)

    def get_portfolio(self, portfolio_id, extended=False):
        interface = 'portfolios{}/{}'. format('/extended' if extended else '', portfolio_id)
        return self._operation(interface)

    def create_portfolios(self, data):
        interface = 'portfolios'
        return self._operation(interface, data, method='POST')

    def update_portfolios(self, data):
        interface = 'portfolios'
        return self._operation(interface, data, method='PUT')

    """ *********************************************************************
    CHANGE HISTORY
    ********************************************************************* """
    def list_changes(self, data):
        interface = 'history'
        return self._operation(interface, data, method='POST', version=None)

    """ *********************************************************************
    PRODUCT ELIGIBILITY
    ********************************************************************* """
    def list_eligibility(self, data):
        interface = 'eligibility/product/list'
        return self._operation(interface, data, method='POST', version=None)

    """ *********************************************************************
    SP CAMPAIGN MANAGEMENT
    ********************************************************************* """
    def get_campaign(self, campaign_id, extended=False):
        interface = 'sp/campaigns{}/{}'.format('/extended' if extended else '', campaign_id)
        return self._operation(interface)

    def create_campaigns(self, data):
        """
        Creates one or more campaigns. Successfully created campaigns will be
        assigned unique **campaignIds**.
        :param data: A list of up to 100 campaigns to be created.  Required
            fields for campaign creation are **name**, **campaignType**,
            **targetingType**, **state**, **dailyBudget** and **startDate**.
        """
        interface = 'sp/campaigns'
        return self._operation(interface, data, method='POST')

    def update_campaigns(self, data):
        """
        Updates one or more campaigns.
        :param data: A list of up to 100 updates containing **campaignIds** and
            the mutable fields to be modified. Mutable fields are **name**,
            **state**, **dailyBudget**, **startDate**, and **endDate**.
        """
        interface = 'sp/campaigns'
        return self._operation(interface, data, method='PUT')


    def archive_campaign(self, campaign_id):
        """
        Sets the campaign status to archived. This same operation can be
        performed via an update, but is included for completeness.
        """
        interface = 'sp/campaigns/{}'.format(campaign_id)
        return self._operation(interface, method='DELETE')

    def list_campaigns(self, data=None, extended=False):
        """
        Retrieves a list of campaigns satisfying optional criteria.
        """
        interface = 'sp/campaigns{}'.format('/extended' if extended else '')
        return self._operation(interface, data)

    """ *********************************************************************
    SP BUDGET RECOMMENDATIONS
    ********************************************************************* """
    def list_budget_recommendations(self, data):
        interface = 'sp/campaigns/budgetRecommendations'
        return self._operation(interface, data, method='POST')

    """ *********************************************************************
    SP AD GROUP MANAGEMENT
    ********************************************************************* """
    def get_ad_group(self, ad_group_id, extended=False):
        interface = 'sp/adGroups{}/{}'.format('/extended' if extended else '', ad_group_id)
        return self._operation(interface)

    def create_ad_groups(self, data):
        interface = 'sp/adGroups'
        return self._operation(interface, data, method='POST')

    def update_ad_groups(self, data):
        interface = 'sp/adGroups'
        return self._operation(interface, data, method='PUT')

    def archive_ad_group(self, ad_group_id):
        interface = 'sp/adGroups/{}'.format(ad_group_id)
        return self._operation(interface, method='DELETE')

    def list_ad_groups(self, data=None, extended=False):
        interface = 'sp/adGroups{}'.format('/extended' if extended else '')
        return self._operation(interface, data)

    """ *********************************************************************
    SP PRODUCT AD MANAGEMENT
    ********************************************************************* """
    def get_product_ad(self, product_ad_id, extended=False):
        interface = 'sp/productAds{}/{}'.format('/extended' if extended else '', product_ad_id)
        return self._operation(interface)

    def create_product_ads(self, data):
        interface = 'sp/productAds'
        return self._operation(interface, data, method='POST')

    def update_product_ads(self, data):
        interface = 'sp/productAds'
        return self._operation(interface, data, method='PUT')

    def archive_product_ad(self, product_ad_id, extended=False):
        interface = 'sp/productAds/{}'.format(product_ad_id)
        return self._operation(interface, method='DELETE')

    def list_product_ads(self, data=None, extended=False):
        interface = 'sp/productAds{}'.format('/extended' if extended else '')
        return self._operation(interface, data)

    """ *********************************************************************
    SP KEYWORD MANAGEMENT
    ********************************************************************* """
    def get_keyword(self, keyword_id, extended=False):
        interface = 'sp/keywords{}/{}'.format('/extended' if extended else '', keyword_id)
        return self._operation(interface)

    def create_keywords(self, data):
        """
        :param data: A list of up to 1000 keywords to be created. Required
            fields for keyword creation are campaignId, adGroupId, keywordText,
            matchType and state.
        """
        interface = 'sp/keywords'
        return self._operation(interface, data, method='POST')

    def update_keywords(self, data):
        interface = 'sp/keywords'
        return self._operation(interface, data, method='PUT')

    def archive_keyword(self, keyword_id):
        interface = 'sp/keywords/{}'.format(keyword_id)
        return self._operation(interface, method='DELETE')

    def list_biddable_keywords(self, data=None, extended=False):
        interface = 'sp/keywords{}'.format('/extended' if extended else '')
        return self._operation(interface, data)

    """ *********************************************************************
    SP SUGGESTED KEYWORDS
    ********************************************************************* """
    def list_suggested_keywords_for_ad_group(self, ad_group_id, extended=False):
        interface = 'sp/adGroups/{}/suggested/keywords{}'.format(ad_group_id, '/extended' if extended else '')
        return self._operation(interface)

    def list_suggested_keywords_for_asin(self, asin):
        interface = 'sp/asins/{}/suggested/keywords'.format(asin)
        return self._operation(interface)

    def list_suggested_keywords_for_asins(self, data):
        interface = 'sp/asins/suggested/keywords'
        return self._operation(interface, data, method='POST')

    """ *********************************************************************
    SP KEYWORD RANK RECOMMENDATIONS
    ********************************************************************* """
    def list_keyword_rank_recommendations(self, data):
        # TODO - determine what should go in data
        interface = 'sp/targets/keywords/recommendation'
        return self._operation(interface, data, method='POST')

    """ *********************************************************************
    SP BID RECOMMENDATIONS
    ********************************************************************* """
    def list_bid_recommendations_for_ad_group(self, ad_group_id):
        interface = 'sp/adGroups/{}/bidRecommendations'.format(ad_group_id)
        return self._operation(interface)

    def list_bid_recommendations_for_keyword(self, keyword_id):
        interface = 'sp/keywords/{}/bidRecommendations'.format(keyword_id)
        return self._operation(interface)

    def list_bid_recommendations_for_keywords(self, ad_group_id, keywords):
        interface = 'sp/keywords/bidRecommendations'
        data = {
            'adGroupId': ad_group_id,
            'keywords': keywords
        }
        return self._operation(interface, data, method='POST')

    def list_bid_recommendations_for_targets(self, ad_group_id, expressions):
        interface = 'sp/targets/bidRecommendations'
        data = {
            'adGroupId': ad_group_id,
            'expressions': expressions
        }
        return self._operation(interface, data, method='POST')

    """ *********************************************************************
    SP NEGATIVE KEYWORD MANAGEMENT
    ********************************************************************* """
    def get_negative_keyword(self, negative_keyword_id, extended=False):
        interface = 'sp/negativeKeywords{}/{}'.format('/extended' if extended else '', negative_keyword_id)
        return self._operation(interface)

    def create_negative_keywords(self, data):
        interface = 'sp/negativeKeywords'
        return self._operation(interface, data, method='POST')

    def update_negative_keywords(self, data):
        interface = 'sp/negativeKeywords'
        return self._operation(interface, data, method='PUT')

    def archive_negative_keyword(self, negative_keyword_id):
        interface = 'sp/negativeKeywords/{}'.format(negative_keyword_id)
        return self._operation(interface, method='DELETE')

    def list_negative_keywords(self, data=None, extended=False):
        interface = 'sp/negativeKeywords{}'.format('/extended' if extended else '')
        return self._operation(interface, data)

    """ *********************************************************************
    SP CAMPAIGN NEGATIVE KEYWORD MANAGEMENT
    ********************************************************************* """
    def get_campaign_negative_keyword(self, campaign_negative_keyword_id, extended=False):
        interface = 'sp/campaignNegativeKeywords{}/{}'.format('/extended' if extended else '', campaign_negative_keyword_id)
        return self._operation(interface)

    def create_campaign_negative_keywords(self, data):
        interface = 'sp/campaignNegativeKeywords'
        return self._operation(interface, data, method='POST')

    def update_campaign_negative_keywords(self, data):
        interface = 'sp/campaignNegativeKeywords'
        return self._operation(interface, data, method='PUT')

    def remove_campaign_negative_keyword(self, campaign_negative_keyword_id):
        interface = 'sp/campaignNegativeKeywords/{}'.format(campaign_negative_keyword_id)
        return self._operation(interface, method='DELETE')

    def list_campaign_negative_keywords(self, data=None, extended=False):
        interface = 'sp/campaignNegativeKeywords{}'.format('/extended' if extended else '')
        return self._operation(interface, data)

    """ *********************************************************************
    SP TARGET MANAGEMENT
    ********************************************************************* """
    def get_target(self, target_id, extended=False):
        interface = 'sp/targets{}/{}'.format('/extended' if extended else '', target_id)
        return self._operation(interface)

    def create_targets(self, data):
        """
        :param data: A list of up to 100 targets to be created.
        """
        interface = 'sp/targets'
        return self._operation(interface, data, method='POST')

    def update_targets(self, data):
        """
        :param data: A list of up to 100 updates containing targetIds and the
            mutable fields to be modified.
        """
        interface = 'sp/targets'
        return self._operation(interface, data, method='PUT')

    def archive_target(self, ad_group_id):
        interface = 'sp/targets/{}'.format(target_id)
        return self._operation(interface, method='DELETE')

    def list_targets(self, data=None, extended=False):
        interface = 'sp/targets{}'.format('/extended' if extended else '')
        return self._operation(interface, data)

    def list_target_brands(self, data=None):
        """ Recommended brands for targeting """
        interface = 'sp/targets/brands'
        return self._operation(interface, data)

    def list_target_categories(self, data=None):
        """ Recommended categories for targeting """
        interface = 'sp/targets/categories'
        return self._operation(interface, data)

    def refine_target_categories(self, data=None):
        """ Refinements for a single category """
        interface = 'sp/targets/categories/refinements'
        return self._operation(interface, data)

    def list_target_product_recommendations(self, data=None):
        """ Recommended products for targeting """
        interface = 'sp/targets/productRecommendations'
        return self._operation(interface, data, method='POST')

    """ *********************************************************************
    SP NEGATIVE TARGET MANAGEMENT
    ********************************************************************* """
    def get_negative_target(self, target_id, extended=False):
        interface = 'sp/negativeTargets{}/{}'.format('/extended' if extended else '', ad_group_id)
        return self._operation(interface)

    def create_negative_targets(self, data):
        interface = 'sp/negativeTargets'
        return self._operation(interface, data, method='POST')

    def update_negative_targets(self, data):
        interface = 'sp/negativeTargets'
        return self._operation(interface, data, method='PUT')

    def archive_negative_target(self, ad_group_id):
        interface = 'sp/negativeTargets/{}'.format(target_id)
        return self._operation(interface, method='DELETE')

    def list_negative_targets(self, data=None, extended=False):
        interface = 'sp/negativeTargets{}'.format('/extended' if extended else '')
        return self._operation(interface, data)

    """ *********************************************************************
    SP REPORTS
    ********************************************************************* """
    def request_report(self, record_type, data={}):
        """
        :POST: /{campaignType}/reports
        """
        interface = 'sp/{}/report'.format(record_type)
        return self._operation(interface, data, method='POST')

    def get_report(self, report_id):
        interface = 'reports/{}'.format(report_id)
        res = self._operation(interface)
        if res['code'] == 200 and json.loads(res['response'])['status'] == 'SUCCESS':
            return self._download(location=json.loads(res['response'])['location'])
        else:
            return res

    """ *********************************************************************
    SP SNAPSHOTS
    ********************************************************************* """
    def request_snapshot(self, record_type, data={}):
        interface = 'sp/{}/snapshot'.format(record_type)
        return self._operation(interface, data, method='POST')

    def get_snapshot(self, snapshot_id):
        interface = 'snapshots/{}'.format(snapshot_id)
        res = self._operation(interface)
        if res['code'] == 200 and json.loads(res['response'])['status'] == 'SUCCESS':
            return self._download(location=json.loads(res['response'])['location'])
        else:
            return res



    """ *********************************************************************
    SB / TO REMOVE
    ********************************************************************* """


    def get_sb_keyword_bid_recommendations(self, campaign_id, keywords):
        interface = 'recommendations/bids'
        data = {
            'campaignId': campaign_id,
            'keywords': keywords
        }

        return self._operation(interface, data, method='POST')

    def get_sb_target_bid_recommendations(self, campaign_id, keywords):
        interface = 'recommendations/bids'

        data = {
            'campaignId': campaign_id,
            'targets': keywords
        }

        return self._operation(interface, data, method='POST')

    def create_search_terms(self, data):
        """
        Creates one search terms report.

        :POST: /targets/report
        :param data: keyword search terms report to be created.
        :type data: dictionary

        :returns:
            :202: report response
            :401: Unauthorized
        """
        interface = 'sp/targets/report'
        return self._operation(interface, data, method='POST')

    def create_search_terms_old(self, data):
        """
        Creates one search terms report.

        :POST: /keywords/report
        :param data:  keyword search terms report to be created.
        :type data: dictionary

        :returns:
            :202: report response
            :401: Unauthorized
        """
        interface = 'sp/keywords/report'
        return self._operation(interface, data, method='POST')


    def request_report(self, record_type=None, report_id=None, data=None, campaign_type='sp'):
        """
        :POST: /{campaignType}/reports

        :param campaign_type: The campaignType to request the report for ('sp' or 'hsa')
          Defaults to 'sp'
        :type data: string
        """
        if record_type is not None:
            interface = '{}/{}/report'.format(campaign_type, record_type)
            return self._operation(interface, data, method='POST')
        elif report_id is not None:
            interface = 'reports/{}'.format(report_id)
            return self._operation(interface)
        else:
            return {'success': False,
                    'code': 0,
                    'response': 'record_type and report_id are both empty.'}

    def get_report(self, report_id):
        interface = 'reports/{}'.format(report_id)
        res = self._operation(interface)
        if res['code'] == 200 and json.loads(res['response'])['status'] == 'SUCCESS':
            res = self._download(
                location=json.loads(res['response'])['location'])
            return res
        else:
            return res

    def request_snapshot(self, record_type=None, snapshot_id=None, data=None, campaign_type='sp'):
        """
        :POST: /snapshots

        Required data:
        * :campaignType: The type of campaign for which snapshot should be
          generated. Must be one of 'sponsoredProducts' or 'headlineSearch'
          Defaults to 'sponsoredProducts.
        """
        if not data:
            data = {}

        if record_type is not None:
            interface = '{}/{}/snapshot'.format(campaign_type, record_type)
            return self._operation(interface, data, method='POST')
        elif snapshot_id is not None:
            interface = 'snapshots/{}'.format(snapshot_id)
            return self._operation(interface, data)
        else:
            return {'success': False,
                    'code': 0,
                    'response': 'record_type and snapshot_id are both empty.'}

    def get_snapshot(self, snapshot_id):
        interface = 'snapshots/{}'.format(snapshot_id)
        res = self._operation(interface)
        if json.loads(res['response'])['status'] == 'SUCCESS':
            res = self._download(
                location=json.loads(res['response'])['location'])
            return res
        else:
            return res


    """ *********************************************************************
    INTERNAL METHODS
    ********************************************************************* """

    def _download(self, location):
        headers = {'Authorization': 'Bearer {}'.format(self._access_token),
                   'Content-Type': 'application/json',
                   'User-Agent': self.user_agent}

        if self.profile_id is not None:
            headers['Amazon-Advertising-API-Scope'] = self.profile_id
        else:
            raise ValueError('Invalid profile Id.')

        opener = urllib.request.build_opener(NoRedirectHandler())
        urllib.request.install_opener(opener)
        req = urllib.request.Request(url=location, headers=headers, data=None)
        try:
            response = urllib.request.urlopen(req)
            if 'location' in response:
                if response['location'] is not None:
                    req = urllib.request.Request(url=response['location'])
                    res = urllib.request.urlopen(req)
                    res_data = res.read()
                    buf = BytesIO(res_data)
                    f = gzip.GzipFile(fileobj=buf)
                    data = f.read()
                    return {'success': True,
                            'code': res.code,
                            'response': json.loads(data.decode('utf-8'))}
                else:
                    return {'success': False,
                            'code': response.code,
                            'response': 'Location is empty.'}
            else:
                return {'success': False,
                        'code': response.code,
                        'response': 'Location not found.'}
        except urllib.error.HTTPError as e:
            return {'success': False,
                    'code': e.code,
                    'response': '{msg}: {details}'.format(msg=e.msg, details=e.read())}

    def _operation(self, interface, params=None, method='GET', version='v2'):
        if version is None:
            use_version = ''
        else:
            use_version = '/{}'.format(version)
        """
        Makes that actual API call.

        :param interface: Interface used for this call.
        :type interface: string
        :param params: Parameters associated with this call.
        :type params: GET: string POST: dictionary
        :param method: Call method. Should be either 'GET', 'PUT', or 'POST'
        :type method: string
        """
        if self._access_token is None:
            return {'success': False,
                    'code': 0,
                    'response': 'access_token is empty.'}

        headers = {'Authorization': 'Bearer {}'.format(self._access_token),
                   'Amazon-Advertising-API-ClientId': self.client_id,
                   'Content-Type': 'application/json',
                   'User-Agent': self.user_agent}

        if self.sandbox:
            headers['BIDDING_CONTROLS_ON'] = 'true'

        if self.profile_id is not None and self.profile_id != '':
            headers['Amazon-Advertising-API-Scope'] = self.profile_id
        elif 'profiles' not in interface:
            # Profile ID is required for all calls beyond authentication and getting profile info
            return {'success': False,
                    'code': 0,
                    'response': 'profile_id is empty.'}

        data = None

        if method == 'GET':
            if params is not None:
                p = '?{}'.format(urllib.parse.urlencode(params))
            else:
                p = ''

            url = 'https://{host}{api_version}/{interface}{params}'.format(
                host=self.endpoint,
                api_version=use_version,
                interface=interface,
                params=p)
        else:
            if params is not None:
                data = json.dumps(params).encode('utf-8')

            url = 'https://{host}{api_version}/{interface}'.format(
                host=self.endpoint,
                api_version=use_version,
                interface=interface)

        if PYTHON == 3:
            req = urllib.request.Request(url=url, headers=headers, data=data)
        else:
            req = MethodRequest(url=url, headers=headers, data=data, method=method)
        req.method = method

        try:
            f = urllib.request.urlopen(req)
            return {'success': True,
                    'code': f.code,
                    'response': f.read().decode('utf-8')}
        except urllib.error.HTTPError as e:
            return {'success': False,
                    'code': e.code,
                    'response': '{msg}: {details}'.format(msg=e.msg, details=e.read())}


class NoRedirectHandler(urllib.request.HTTPErrorProcessor):
    """Handles report and snapshot redirects."""

    def http_response(self, request, response):
        if response.code == 307:
            if 'Location' in response.headers:
                return {'code': 307,
                        'location': response.headers['Location']}
            else:
                return {'code': response.code, 'location': None}
        else:
            return urllib.request.HTTPErrorProcessor.http_response(
                self, request, response)

    https_response = http_response


class MethodRequest(urllib.request.Request):
    """
    When not using Python 3 and the requests library.
    Source: Ed Marshall, https://gist.github.com/logic/2715756
    """
    def __init__(self, *args, **kwargs):
        if 'method' in kwargs:
            self._method = kwargs['method']
            del kwargs['method']
        else:
            self._method = None
        return urllib.request.Request.__init__(self, *args, **kwargs)

    def get_method(self, *args, **kwargs):
        if self._method is not None:
            return self._method
        return urllib.request.Request.get_method(self, *args, **kwargs)
