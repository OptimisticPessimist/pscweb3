import { Helmet } from 'react-helmet-async';

interface PageHeadProps {
    title?: string;
}

export const PageHead = ({ title }: PageHeadProps) => {
    const fullTitle = title ? `PSCWEB3 -${title}-` : 'PSCWEB3';
    return (
        <Helmet>
            <title>{fullTitle}</title>
        </Helmet>
    );
};
